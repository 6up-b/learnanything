---
title: "learnloop.figure_admission"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figure_admission.py"
source_paths:
  - "src/learnloop/figure_admission.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figure_admission module"
  - "src/learnloop/figure_admission.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.figure_admission`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figure_admission` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Reader RW5a: the figure switch, and the one gate every figure-derived model request passes.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py) |
| Source lines | 472 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `figures_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 40) — ``figures.enabled`` of ``vault`` (a loaded vault or its config): the one predicate, defaulting to off when there is no ``figures`` section.
- `figure_home_keys(connection: Any, figure_id: str) -> list[tuple[str, str]] | None` ([source](../../../../../src/learnloop/figure_admission.py), line 54) — Reader RW5d (Codex review F3, F4): where a figure built with no passage lands, as ``(extraction_id, span_id)``: the reading position of every request that built or reused it or a version it supersedes, first asked first.
- `offerable(block_type: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 111) — Whether a cited block is one "make this explorable" may be offered on: code decides the block (by its extracted type), the judge only whether it could support a figure.
- `offer_kind(block_type: Any) -> str | None` ([source](../../../../../src/learnloop/figure_admission.py), line 119) — ``equation`` | ``figure`` for an offerable block, else None.
- `offerable_blocks(repository: Any, keys: Any) -> dict[tuple[str, str], str]` ([source](../../../../../src/learnloop/figure_admission.py), line 127) — Which of these ``(extraction_id, span_id)`` blocks an offer may name, each with its kind (:func:`offer_kind`), read from the stored blocks.
- `explorable_yes(value: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 149) — The judge said yes (an old output with no field, or anything else, is no).
- `tutor_explorable_judgment_id(question_event_id: str, extraction_id: str, span_id: str) -> str` ([source](../../../../../src/learnloop/figure_admission.py), line 162) — The ledger id of the tutor's verdict on one block of one answer: derived, so the press reads it back without a search, and an answer judges a block once.
- `tutor_explorable_yes(repository: Any, question_event_id: str, keys: Any) -> set[tuple[str, str]]` ([source](../../../../../src/learnloop/figure_admission.py), line 171) — Which of these ``(extraction_id, span_id)`` blocks the tutor's ledger rows for this answer record as ``explorable: yes``.
- `tutor_figure_goal_judgment_id(question_event_id: str) -> str` ([source](../../../../../src/learnloop/figure_admission.py), line 199) — The ledger id of an answer's figure goal: derived, so the press reads it back without a search, and an answer offers at most one goal.
- `figure_goal_digest(text: Any, span_keys: Any) -> str` ([source](../../../../../src/learnloop/figure_admission.py), line 208) — The identity of a figure goal: its whitespace-normalized text and the cited passages it is grounded in, in order.
- `tutor_figure_goal_offered(repository: Any, question_event_id: str, text: Any, span_keys: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 218) — Whether the answer's ledger row records this very goal (its text and its grounding keys) as offered by the tutor's model.
- `rich_tiers_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 235) — Reader RW5d P2b: ``figures.rich_tiers_enabled`` under ``figures.enabled``: the rich tiers (a narrated Manim figure; JS behind its build flag).
- `author_learner_state_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 245) — Learner data-relax 2: ``figures.author_learner_state`` under ``figures.enabled``: the figure author is sent the learner's state on the passage's topics (``learnloop.figures.learner_state``).
- `help_kind_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 255) — Reader RW5d P3: ``figures.help_kind_enabled`` under ``figures.enabled``: figures inside an open attempt (the Ask panel's *show me* on practice, feedback and the workbench, the cold take step, the chooser's ``explore_figure``, ``figure`` in the help outcomes).
- `teacher_visuals_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 267) — ``teacher.visuals``: the teacher's manipulatives in a lesson.
- `manim_opt_in(vault: Any) -> str | None` ([source](../../../../../src/learnloop/figure_admission.py), line 278) — Reader RW5d P2b: the learner's standing opt-in for Manim figures (``"standing"``), their "not now" (``"declined"``), or None (not asked).
- `text_key(vault: Any) -> Hashable` ([source](../../../../../src/learnloop/figure_admission.py), line 287) — What a figure prediction's learner-text reading depends on: the vault and the switch (its money cap is ``learner_text_gaps``'s, as on main).
- `class FiguresChanged(BaseException)` ([source](../../../../../src/learnloop/figure_admission.py), line 294) — A figure-derived request refused before it was sent: the configuration its unit of work started under has changed (the switch turned off, the route, cap or price changed, or another vault is open).
- `class HoldReason(str)` ([source](../../../../../src/learnloop/figure_admission.py), line 319) — A hold's reason: the prose the unit's error carries, as before, with the code the gate's record keeps (a record holds codes, never prose).
  - `__new__(cls, text: str, code: str) -> HoldReason` (line 325; internal)
- `hold_reason(text: str | None, code: str) -> str | None` ([source](../../../../../src/learnloop/figure_admission.py), line 331) — ``text`` with its hold ``code`` (None and the empty string pass through: no hold).
- `class FiguresGate` ([source](../../../../../src/learnloop/figure_admission.py), line 337) — Admit a figure-derived unit of work's requests only while its key holds.
  - `__init__(self, vault: Any, key: Callable[[Any], Hashable], *, live_vault: Callable[[], Any] | None=None, hold: Callable[[Any], str | None] | None=None, wait: Callable[[], Any] | None=None, repository: Any=None) -> None` (line 361; internal)
  - `_current(self) -> Any | None` (line 387; internal)
  - `check(self, purpose: str='request') -> None` (line 397; public) — Raise :class:`FiguresChanged` when the unit may do nothing more.
  - `admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any` (line 426; public)
  - `settle(self, admission: Any, usage: dict[str, Any]) -> None` (line 439; public)

### Module constants

- `GROUNDING_PASSAGES` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 51)
- `OFFER_BLOCK_TYPES` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 105)
- `EXPLORABLE` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 108)
- `TUTOR_EXPLORABLE_TASK` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 159)
- `TUTOR_FIGURE_GOAL_TASK` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 194)
- `FIGURE_GOAL_OFFERED` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 196)
- `GATE_RULES` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 311)
- `HOLD_CODES` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 315)

### Explicit exports

`__all__` declares:

- `EXPLORABLE`
- `FiguresChanged`
- `FiguresGate`
- `HOLD_CODES`
- `HoldReason`
- `OFFER_BLOCK_TYPES`
- `FIGURE_GOAL_OFFERED`
- `TUTOR_EXPLORABLE_TASK`
- `TUTOR_FIGURE_GOAL_TASK`
- `author_learner_state_enabled`
- `help_kind_enabled`
- `hold_reason`
- `explorable_yes`
- `figure_goal_digest`
- `figure_home_keys`
- `figures_enabled`
- `manim_opt_in`
- `offer_kind`
- `offerable`
- `offerable_blocks`
- `rich_tiers_enabled`
- `teacher_visuals_enabled`
- `text_key`
- `tutor_explorable_judgment_id`
- `tutor_explorable_yes`
- `tutor_figure_goal_judgment_id`
- `tutor_figure_goal_offered`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/split/figure_trace|learnloop.diagnosis.split.figure_trace]] — imports `help_kind_enabled`; statically calls `help_kind_enabled`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `FiguresChanged`, `FiguresGate`, `text_key`; statically calls `FiguresGate`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `figure_home_keys`, `figures_enabled`; statically calls `figure_home_keys`, `figures_enabled`
- [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]] — imports `FiguresChanged`, `FiguresGate`, `figures_enabled`, `hold_reason`, `rich_tiers_enabled`; statically calls `FiguresGate`, `figures_enabled`, `hold_reason`, `rich_tiers_enabled`
- [[Reference/Modules/learnloop/figures/grounding|learnloop.figures.grounding]] — imports `FiguresChanged`, `GROUNDING_PASSAGES`
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `figure_home_keys`, `help_kind_enabled`; statically calls `figure_home_keys`, `help_kind_enabled`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `author_learner_state_enabled`; statically calls `author_learner_state_enabled`
- [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]] — imports `figures_enabled`, `rich_tiers_enabled`; statically calls `figures_enabled`, `rich_tiers_enabled`
- [[Reference/Modules/learnloop/figures/power|learnloop.figures.power]] — imports `hold_reason`; statically calls `hold_reason`
- [[Reference/Modules/learnloop/figures/predictions|learnloop.figures.predictions]] — imports `figures_enabled`; statically calls `figures_enabled`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `FiguresChanged`, `FiguresGate`, `figures_enabled`; statically calls `FiguresGate`, `figures_enabled`
- [[Reference/Modules/learnloop/figures/protection|learnloop.figures.protection]] — imports `figure_home_keys`, `figures_enabled`; statically calls `figure_home_keys`, `figures_enabled`
- [[Reference/Modules/learnloop/figures/request|learnloop.figures.request]] — imports `author_learner_state_enabled`, `figures_enabled`, `help_kind_enabled`, `rich_tiers_enabled`, `teacher_visuals_enabled`; statically calls `author_learner_state_enabled`, `figures_enabled`, `help_kind_enabled`, `rich_tiers_enabled`, `teacher_visuals_enabled`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `FiguresChanged`, `FiguresGate`, `author_learner_state_enabled`, `figures_enabled`, `hold_reason`, `manim_opt_in`, `rich_tiers_enabled`; statically calls `FiguresGate`, `author_learner_state_enabled`, `figures_enabled`, `hold_reason`, `manim_opt_in`, `rich_tiers_enabled`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `figures_enabled`; statically calls `figures_enabled`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `FiguresChanged`, `FiguresGate`, `figures_enabled`; statically calls `FiguresGate`, `figures_enabled`
- [[Reference/Modules/learnloop/figures/view|learnloop.figures.view]] — imports `rich_tiers_enabled`; statically calls `rich_tiers_enabled`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `EXPLORABLE`, `explorable_yes`, `figures_enabled`, `offer_kind`; statically calls `explorable_yes`, `figures_enabled`, `offer_kind`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `offerable_blocks`; statically calls `offerable_blocks`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `figures_enabled`, `teacher_visuals_enabled`; statically calls `figures_enabled`, `teacher_visuals_enabled`
- [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]] — imports `GROUNDING_PASSAGES`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `FIGURE_GOAL_OFFERED`, `TUTOR_EXPLORABLE_TASK`, `TUTOR_FIGURE_GOAL_TASK`, `explorable_yes`, `figure_goal_digest`, `figures_enabled`, `offerable_blocks`, `tutor_explorable_judgment_id`, `tutor_figure_goal_judgment_id`; statically calls `explorable_yes`, `figure_goal_digest`, `figures_enabled`, `offerable_blocks`, `tutor_explorable_judgment_id`, `tutor_figure_goal_judgment_id`
- [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]] — imports `help_kind_enabled`; statically calls `help_kind_enabled`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `help_kind_enabled`; statically calls `help_kind_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `figures_enabled`; statically calls `figures_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `figures_enabled`, `help_kind_enabled`, `manim_opt_in`, `offerable_blocks`, `rich_tiers_enabled`, `tutor_explorable_yes`, `tutor_figure_goal_offered`; statically calls `figures_enabled`, `help_kind_enabled`, `manim_opt_in`, `offerable_blocks`, `rich_tiers_enabled`, `tutor_explorable_yes`, `tutor_figure_goal_offered`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `help_kind_enabled`; statically calls `help_kind_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `figures_enabled`; statically calls `figures_enabled`
- [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]] — imports `figures_enabled`, `rich_tiers_enabled`; statically calls `figures_enabled`, `rich_tiers_enabled`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `active_request_gate`, `content_key`; calls `active_request_gate`, `content_key`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `judgments_by_ids`; calls `judgments_by_ids`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`; calls `blocks_by_key`
- [[Reference/Modules/learnloop/refusal_records|learnloop.refusal_records]] — imports `module`; calls `figure_gate_record`, `write`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/split/figure_trace|learnloop.diagnosis.split.figure_trace]], [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]], [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]], [[Reference/Modules/learnloop/figures/grounding|learnloop.figures.grounding]] and 24 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_offers.py](../../../../../tests/test_figure_offers.py) — direct import
  - `test_an_offered_build_is_admitted_under_the_builds_key_and_stops_when_figures_go_off`
  - `test_code_decides_the_block_and_only_yes_is_a_yes`
- [tests/test_figure_request_records.py](../../../../../tests/test_figure_request_records.py) — direct import
  - `test_a_hold_with_no_code_is_recorded_unclassified`
  - `test_a_rich_prebuild_whose_item_became_protected_holds_for_it`
  - `test_every_code_is_staged`
- [tests/test_figure_switch_predicates.py](../../../../../tests/test_figure_switch_predicates.py) — direct import
  - `test_the_teachers_visuals_switch_is_the_teachers_alone_and_a_lesson_asks_both`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f16_the_gate_waits_before_it_reads_the_vault_it_checks`
- [tests/test_figures_rw5b_fix_round2.py](../../../../../tests/test_figures_rw5b_fix_round2.py) — direct import
  - `test_a_library_note_pointing_at_another_tasks_yes_row_is_refused`
- [tests/test_figures_rw5b_review.py](../../../../../tests/test_figures_rw5b_review.py) — direct import
  - `test_a_reader_ask_answer_offers_and_its_press_builds_from_its_question_event`
- [tests/test_figures_show_me_codex_review.py](../../../../../tests/test_figures_show_me_codex_review.py) — direct import
  - `test_f6_a_goal_in_the_view_with_no_ledger_row_is_refused`
  - `test_f6_no_goal_writes_no_goal_row`
  - `test_f6_the_tutors_goal_has_one_ledger_row_and_the_press_reads_it`
- [tests/test_refusal_records.py](../../../../../tests/test_refusal_records.py) — direct import
  - `test_the_figure_gate_records_its_first_refusal_once`
- [tests/test_rw5c_source_check.py](../../../../../tests/test_rw5c_source_check.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains figure admission within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
