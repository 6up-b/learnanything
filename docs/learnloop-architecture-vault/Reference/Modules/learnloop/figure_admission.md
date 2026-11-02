---
title: "learnloop.figure_admission"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figure_admission.py"
source_paths:
  - "src/learnloop/figure_admission.py"
source_commit: "a2907d6325e0f83c6311a779f48e4f09314a6f98"
source_commit_timestamp: "2026-11-01T19:47:12-05:00"
source_worktree_state: "clean"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figure_admission` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Reader RW5a: the figure switch, and the one gate every figure-derived model request passes.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py) |
| Source lines | 437 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a2907d6325e0f83c6311a779f48e4f09314a6f98` |
| Commit timestamp | `2026-11-01T19:47:12-05:00` |

## Public API

- `figures_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 39) — ``figures.enabled`` of ``vault`` (a loaded vault or its config): the one predicate, defaulting to off when there is no ``figures`` section.
- `advanced_panels_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 47) — RW5b: ``figures.advanced_panels_enabled`` under ``figures.enabled`` (heat maps, vector fields, trajectories and iterated maps).
- `offers_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 55) — RW5b: ``figures.offers_enabled`` under ``figures.enabled``: the library organizer and the Reader tutor judge ``explorable`` on a cited equation or figure block in the call they already make.
- `show_me_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 70) — Reader RW5d P1: ``figures.show_me_enabled`` under ``figures.enabled``: "show me" takes the learner's words (and the Reader tutor may write an optional figure goal).
- `sketch_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 81) — Reader RW5d P2: ``figures.sketch_enabled`` under ``figures.enabled``: the sketch tier (a sealed, verified simulation when the grammar can't express the idea).
- `figure_home_keys(connection: Any, figure_id: str) -> list[tuple[str, str]] | None` ([source](../../../../../src/learnloop/figure_admission.py), line 91) — Reader RW5d (Codex review F3, F4): where a figure built with no passage lands, as ``(extraction_id, span_id)``: the reading position of every request that built or reused it or a version it supersedes, first asked first.
- `offerable(block_type: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 148) — Whether a cited block is one "make this explorable" may be offered on: code decides the block (by its extracted type), the judge only whether it could support a figure.
- `offer_kind(block_type: Any) -> str | None` ([source](../../../../../src/learnloop/figure_admission.py), line 156) — ``equation`` | ``figure`` for an offerable block, else None.
- `offerable_blocks(repository: Any, keys: Any) -> dict[tuple[str, str], str]` ([source](../../../../../src/learnloop/figure_admission.py), line 164) — Which of these ``(extraction_id, span_id)`` blocks an offer may name, each with its kind (:func:`offer_kind`), read from the stored blocks.
- `explorable_yes(value: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 186) — The judge said yes (an old output with no field, or anything else, is no).
- `tutor_explorable_judgment_id(question_event_id: str, extraction_id: str, span_id: str) -> str` ([source](../../../../../src/learnloop/figure_admission.py), line 199) — The ledger id of the tutor's verdict on one block of one answer: derived, so the press reads it back without a search, and an answer judges a block once.
- `tutor_explorable_yes(repository: Any, question_event_id: str, keys: Any) -> set[tuple[str, str]]` ([source](../../../../../src/learnloop/figure_admission.py), line 208) — Which of these ``(extraction_id, span_id)`` blocks the tutor's ledger rows for this answer record as ``explorable: yes``.
- `tutor_figure_goal_judgment_id(question_event_id: str) -> str` ([source](../../../../../src/learnloop/figure_admission.py), line 236) — The ledger id of an answer's figure goal: derived, so the press reads it back without a search, and an answer offers at most one goal.
- `figure_goal_digest(text: Any, span_keys: Any) -> str` ([source](../../../../../src/learnloop/figure_admission.py), line 245) — The identity of a figure goal: its whitespace-normalized text and the cited passages it is grounded in, in order.
- `tutor_figure_goal_offered(repository: Any, question_event_id: str, text: Any, span_keys: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 255) — Whether the answer's ledger row records this very goal (its text and its grounding keys) as offered by the tutor's model.
- `rich_tiers_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 272) — Reader RW5d P2b: ``figures.rich_tiers_enabled`` under ``figures.enabled``: the rich tiers (a narrated Manim figure; JS behind its build flag).
- `author_learner_state_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 282) — Learner data-relax 2: ``figures.author_learner_state`` under ``figures.enabled``: the figure author is sent the learner's state on the passage's topics (``learnloop.figures.learner_state``).
- `help_kind_enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/figure_admission.py), line 292) — Reader RW5d P3: ``figures.help_kind_enabled`` under ``figures.enabled`` and ``figures.show_me_enabled``: figures inside an open attempt (the Ask panel's *show me* on practice, feedback and the workbench, the cold take step, the chooser's ``explore_figure``, ``figure`` in the hel…
- `manim_opt_in(vault: Any) -> str | None` ([source](../../../../../src/learnloop/figure_admission.py), line 304) — Reader RW5d P2b: the learner's standing opt-in for Manim figures (``"standing"``), their "not now" (``"declined"``), or None (not asked).
- `text_key(vault: Any) -> Hashable` ([source](../../../../../src/learnloop/figure_admission.py), line 313) — What a figure prediction's learner-text reading depends on: the vault and the switch (its money cap is ``learner_text_gaps``'s, as on main).
- `class FiguresChanged(BaseException)` ([source](../../../../../src/learnloop/figure_admission.py), line 320) — A figure-derived request refused before it was sent: the configuration its unit of work started under has changed (the switch turned off, the route, cap or price changed, or another vault is open).
- `class FiguresGate` ([source](../../../../../src/learnloop/figure_admission.py), line 336) — Admit a figure-derived unit of work's requests only while its key holds.
  - `__init__(self, vault: Any, key: Callable[[Any], Hashable], *, live_vault: Callable[[], Any] | None=None, hold: Callable[[Any], str | None] | None=None) -> None` (line 349; internal)
  - `_current(self) -> Any | None` (line 364; internal)
  - `check(self, purpose: str='request') -> None` (line 374; public) — Raise :class:`FiguresChanged` when the unit may do nothing more.
  - `admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any` (line 393; public)
  - `settle(self, admission: Any, usage: dict[str, Any]) -> None` (line 406; public)

### Module constants

- `GROUNDING_PASSAGES` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 67)
- `OFFER_BLOCK_TYPES` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 142)
- `EXPLORABLE` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 145)
- `TUTOR_EXPLORABLE_TASK` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 196)
- `TUTOR_FIGURE_GOAL_TASK` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 231)
- `FIGURE_GOAL_OFFERED` ([src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py), line 233)

### Explicit exports

`__all__` declares:

- `EXPLORABLE`
- `FiguresChanged`
- `FiguresGate`
- `OFFER_BLOCK_TYPES`
- `FIGURE_GOAL_OFFERED`
- `TUTOR_EXPLORABLE_TASK`
- `TUTOR_FIGURE_GOAL_TASK`
- `advanced_panels_enabled`
- `author_learner_state_enabled`
- `help_kind_enabled`
- `explorable_yes`
- `figure_goal_digest`
- `figure_home_keys`
- `figures_enabled`
- `manim_opt_in`
- `offer_kind`
- `offerable`
- `offerable_blocks`
- `offers_enabled`
- `rich_tiers_enabled`
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
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `figure_home_keys`, `help_kind_enabled`; statically calls `figure_home_keys`, `help_kind_enabled`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `author_learner_state_enabled`; statically calls `author_learner_state_enabled`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `FiguresChanged`, `FiguresGate`, `author_learner_state_enabled`, `figures_enabled`, `manim_opt_in`, `rich_tiers_enabled`; statically calls `FiguresGate`, `author_learner_state_enabled`, `figures_enabled`, `manim_opt_in`, `rich_tiers_enabled`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `FiguresChanged`, `FiguresGate`, `GROUNDING_PASSAGES`, `advanced_panels_enabled`, `author_learner_state_enabled`, `figure_home_keys`, `figures_enabled`, `help_kind_enabled`, `offers_enabled`, `show_me_enabled`, `sketch_enabled`; statically calls `FiguresGate`, `advanced_panels_enabled`, `author_learner_state_enabled`, `figure_home_keys`, `figures_enabled`, `help_kind_enabled`, `offers_enabled`, `show_me_enabled`, `sketch_enabled`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `EXPLORABLE`, `explorable_yes`, `offer_kind`, `offers_enabled`; statically calls `explorable_yes`, `offer_kind`, `offers_enabled`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `offerable_blocks`; statically calls `offerable_blocks`
- [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]] — imports `GROUNDING_PASSAGES`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `FIGURE_GOAL_OFFERED`, `TUTOR_EXPLORABLE_TASK`, `TUTOR_FIGURE_GOAL_TASK`, `explorable_yes`, `figure_goal_digest`, `offerable_blocks`, `offers_enabled`, `show_me_enabled`, `tutor_explorable_judgment_id`, `tutor_figure_goal_judgment_id`; statically calls `explorable_yes`, `figure_goal_digest`, `offerable_blocks`, `offers_enabled`, `show_me_enabled`, `tutor_explorable_judgment_id`, `tutor_figure_goal_judgment_id`
- [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]] — imports `help_kind_enabled`; statically calls `help_kind_enabled`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `help_kind_enabled`; statically calls `help_kind_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `manim_opt_in`, `offerable_blocks`, `tutor_explorable_yes`, `tutor_figure_goal_offered`; statically calls `manim_opt_in`, `offerable_blocks`, `tutor_explorable_yes`, `tutor_figure_goal_offered`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `help_kind_enabled`; statically calls `help_kind_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `offers_enabled`, `show_me_enabled`; statically calls `offers_enabled`, `show_me_enabled`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `active_request_gate`, `content_key`; calls `active_request_gate`, `content_key`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `judgments_by_ids`; calls `judgments_by_ids`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`; calls `blocks_by_key`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/split/figure_trace|learnloop.diagnosis.split.figure_trace]], [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]], [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]], [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] and 11 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_offers.py](../../../../../tests/test_figure_offers.py) — direct import
  - `test_code_decides_the_block_and_only_yes_is_a_yes`
  - `test_the_gate_key_of_an_offered_build_includes_the_offers_switch`
- [tests/test_figures_rw5b_fix_round2.py](../../../../../tests/test_figures_rw5b_fix_round2.py) — direct import
  - `test_a_library_note_pointing_at_another_tasks_yes_row_is_refused`
- [tests/test_figures_rw5b_review.py](../../../../../tests/test_figures_rw5b_review.py) — direct import
  - `test_a_reader_ask_answer_offers_and_its_press_builds_from_its_question_event`
- [tests/test_figures_show_me_codex_review.py](../../../../../tests/test_figures_show_me_codex_review.py) — direct import
  - `test_f6_a_goal_in_the_view_with_no_ledger_row_is_refused`
  - `test_f6_no_goal_writes_no_goal_row`
  - `test_f6_the_tutors_goal_has_one_ledger_row_and_the_press_reads_it`

## Modification guidance

- Make changes here when the responsibility remains figure admission within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figure_admission.py](../../../../../src/learnloop/figure_admission.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
