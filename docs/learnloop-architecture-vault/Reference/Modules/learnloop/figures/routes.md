---
title: "learnloop.figures.routes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/routes.py"
source_paths:
  - "src/learnloop/figures/routes.py"
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
  - "learnloop.figures.routes module"
  - "src/learnloop/figures/routes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.routes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.routes` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: The figure route: ``figure_author`` (spec_reader_workbench_v1 §8.5; W10).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py) |
| Source lines | 613 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `models_off() -> bool` ([source](../../../../../../src/learnloop/figures/routes.py), line 80)
- `class FigureAuthorOutputV1(WireModel)` ([source](../../../../../../src/learnloop/figures/routes.py), line 84)
- `class FigureAuthorOutputV2(WireModel)` ([source](../../../../../../src/learnloop/figures/routes.py), line 95) — RW5d P2: the author's answer with the sketch tier on (spec §8.4).
- `advanced_panels_text() -> str` ([source](../../../../../../src/learnloop/figures/routes.py), line 182)
- `sketch_text() -> str` ([source](../../../../../../src/learnloop/figures/routes.py), line 279)
- `class FigureAuthorOutputV3(WireModel)` ([source](../../../../../../src/learnloop/figures/routes.py), line 291) — RW5d P2b: the author's answer with a rich tier on the menu (spec §8.4): the medium chosen by what best explains the idea, with ``why_this_tier``.
- `rich_status_text(tiers: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/figures/routes.py), line 336) — How the status names the medium (only the media on the menu).
- `tier_menu_text(tiers: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/figures/routes.py), line 360) — The media the author may answer with (spec §8.4): one neutral sentence each, in order.
- `rich_text() -> str` ([source](../../../../../../src/learnloop/figures/routes.py), line 367)
- `rich_menu(tiers: Sequence[str] | None) -> tuple[str, ...] | None` ([source](../../../../../../src/learnloop/figures/routes.py), line 392) — The menu when it includes a rich tier (V3), else None (V1/V2 exactly).
- `author_instructions(*, advanced: bool=False, show_me: bool=False, sketch: bool=False, tiers: Sequence[str] | None=None, learner: bool=False) -> str` ([source](../../../../../../src/learnloop/figures/routes.py), line 400)
- `author_prompt_version(*, advanced: bool=False, show_me: bool=False, sketch: bool=False, tiers: Sequence[str] | None=None, learner: bool=False) -> str` ([source](../../../../../../src/learnloop/figures/routes.py), line 430)
- `author_prompt(context: dict[str, Any], *, advanced: bool=False, show_me: bool=False, sketch: bool=False, tiers: Sequence[str] | None=None, learner: bool=False) -> str` ([source](../../../../../../src/learnloop/figures/routes.py), line 440)
- `output_model(*, sketch: bool=False, tiers: Sequence[str] | None=None) -> type[WireModel]` ([source](../../../../../../src/learnloop/figures/routes.py), line 450) — The author's output contract: RW5b's V1 off, V2 with the sketch tier on, V3 (RW5d P2b) with a rich tier on the menu.
- `class FigureUnavailable(Exception)` ([source](../../../../../../src/learnloop/figures/routes.py), line 459) — A figure route cannot be called (``reason``: ``models_off`` | ``unrouted`` | ``unpriced`` | ``capped`` | ``unavailable`` | ``no_image_input``); ``message`` is the learner's line.
  - `__init__(self, reason: str, message: str) -> None` (line 464; internal)
- `daily_envelope(vault: Any, repository: Repository, *, clock: Clock | None=None) -> SharedDailyEnvelope` ([source](../../../../../../src/learnloop/figures/routes.py), line 470)
- `class FigureRoute` ([source](../../../../../../src/learnloop/figures/routes.py), line 477) — The author route pinned for one request, with its call cap.
  - `__init__(self, vault: Any, repository: Repository, task: str, *, client: Any | None, envelope: Any, owner_id: str, max_calls: int) -> None` (line 486; internal)
  - `bind_owner(self, owner_id: str) -> None` (line 500; public) — Name the request the calls' receipts belong to (known only once the input is hashed, after the route was asked whether it reads images).
  - `subscription(self) -> bool` (line 509; public)
  - `problem(self) -> FigureUnavailable | None` (line 512; public)
  - `resolve(self) -> Any` (line 528; public)
  - `reads_images(self) -> bool` (line 555; public)
  - `ask(self, prompt: str, result_model: type[WireModel], *, images: tuple[tuple[str, bytes], ...]=(), metadata: dict[str, Any] | None=None) -> Any` (line 562; public)
  - `model(self) -> str | None` (line 576; public)

### Module constants

- `AUTHOR_TASK` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 70)
- `AUTHOR_PROMPT_VERSION` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 72)
- `ENVELOPE` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 73)
- `OWNER_KINDS` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 75)
- `MODELS_ENV` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 76)
- `MAX_AUTHOR_ATTEMPTS` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 77)
- `GRAMMAR_TEXT` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 111)
- `SPEC_TEXT` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 122)
- `AUTHOR_INSTRUCTIONS` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 142)
- `ADVANCED_PROMPT_VERSION` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 161)
- `ADVANCED_PANELS_TEXT` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 163)
- `_UNSUPPORTED_V1` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 194)
- `_UNSUPPORTED_V2` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 195)
- `SHOW_ME_SUFFIX` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 202)
- `SHOW_ME_TEXT` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 204)
- `SKETCH_SUFFIX` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 218)
- `_STATUS_V1` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 221)
- `_STATUS_V1_PANELS` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 226)
- `STATUS_V2` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 229)
- `SKETCH_TEXT` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 237)
- `RICH_SUFFIX` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 314)
- `TIER_SENTENCES` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 318)
- `RICH_CHOICE_TEXT` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 330)
- `RICH_TEXT` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 350)
- `LEARNER_SUFFIX` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 378)
- `LEARNER_STATE_TEXT` ([src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py), line 380)

### Explicit exports

`__all__` declares:

- `ADVANCED_PROMPT_VERSION`
- `AUTHOR_PROMPT_VERSION`
- `AUTHOR_TASK`
- `ENVELOPE`
- `FigureAuthorOutputV1`
- `FigureAuthorOutputV2`
- `FigureAuthorOutputV3`
- `FigureRoute`
- `FigureUnavailable`
- `LEARNER_STATE_TEXT`
- `LEARNER_SUFFIX`
- `MAX_AUTHOR_ATTEMPTS`
- `MODELS_ENV`
- `OWNER_KINDS`
- `RICH_SUFFIX`
- `SHOW_ME_SUFFIX`
- `SHOW_ME_TEXT`
- `SKETCH_SUFFIX`
- `SKETCH_TEXT`
- `STATUS_V2`
- `advanced_panels_text`
- `author_instructions`
- `author_prompt`
- `author_prompt_version`
- `daily_envelope`
- `models_off`
- `output_model`
- `rich_menu`
- `sketch_text`
- `tier_menu_text`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `FigureRoute`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `module`; statically calls `FigureRoute`, `daily_envelope`, `models_off`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `FigureRoute`, `author_prompt`, `author_prompt_version`, `daily_envelope`, `output_model`, `rich_menu`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `spend_envelopes`; calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `IMAGE_INPUT`, `ISOLATED_TURN`, `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `RICH_BRIEF_MAX`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `module`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `module`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`; calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SharedDailyEnvelope`, `midnight`; calls `SharedDailyEnvelope`, `midnight`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `os`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iii_a_figure_grant_never_meters_an_ask_and_an_ask_grant_meters_it_under_the_cap`
- [tests/test_figure_author_predictions.py](../../../../../../tests/test_figure_author_predictions.py) — direct import
  - `test_both_prompts_spell_the_shape_out_under_new_versions`
- [tests/test_figure_decision_records.py](../../../../../../tests/test_figure_decision_records.py) — direct import
  - `test_a_refused_build_leaves_a_refused_record`
- [tests/test_figure_offers.py](../../../../../../tests/test_figure_offers.py) — direct import
  - `test_a_build_stops_when_the_advanced_panels_are_switched_off_mid_build`
  - `test_a_selection_build_does_not_stop_for_the_offers_switch`
  - `test_an_offered_build_stops_when_offers_are_switched_off_before_its_request`
  - `test_the_author_prompt_is_rw5a_byte_for_byte_while_the_panels_are_off`
  - `test_with_the_panels_off_the_author_may_not_emit_them_and_stored_ones_are_cant_draw`
  - `test_with_the_panels_on_the_author_is_told_of_them_and_a_field_is_shown`
- [tests/test_figure_region.py](../../../../../../tests/test_figure_region.py) — direct import
  - `test_an_image_request_is_refused_by_a_transport_that_cannot_read_images`
  - `test_the_openai_chat_transport_sends_image_parts_only_for_an_image_profile`
- [tests/test_figure_rich_contract.py](../../../../../../tests/test_figure_rich_contract.py) — direct import
  - `test_the_menu_is_neutral_facts_in_order_golden`
  - `test_v3_instructions_replace_the_preference_and_carry_the_rich_brief`
  - `test_with_no_rich_tier_on_the_menu_the_contract_is_v2s_byte_for_byte`
- [tests/test_figures_rw5b_review.py](../../../../../../tests/test_figures_rw5b_review.py) — direct import
  - `test_a_figure_built_before_the_panels_came_on_is_reused_with_them_on`
- [tests/test_figures_scope_redesign.py](../../../../../../tests/test_figures_scope_redesign.py) — direct import
  - `test_no_code_path_can_store_or_render_verified_or_checked`
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_a_goal_alone_is_grounded_in_the_books_and_lands_where_the_learner_was`
  - `test_an_rw5ab_request_hashes_and_prompts_exactly_as_before`
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_switched_off_the_payload_prompt_and_key_are_the_predecessors_byte_for_byte`
  - `test_the_learner_state_reaches_the_author_and_protected_work_never_does`
  - `test_the_reuse_key_and_prompt_version_name_the_state_only_when_non_empty`
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_a_lesson_figure_never_spawns_a_rich_job`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_a_sketch_answer_is_verified_stored_and_shown_with_its_check_lines`
  - `test_off_the_contract_prompt_and_key_are_rw5bs_byte_for_byte`
  - `test_the_tier_judgment_has_a_receipt_with_its_reason`
  - `test_with_the_tier_on_a_spec_answer_is_still_a_grammar_figure_with_a_receipt`

## Modification guidance

- Make changes here when the responsibility remains routes within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/routes.py](../../../../../../src/learnloop/figures/routes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
