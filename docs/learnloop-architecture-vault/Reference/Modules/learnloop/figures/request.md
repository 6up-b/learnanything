---
title: "learnloop.figures.request"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/request.py"
source_paths:
  - "src/learnloop/figures/request.py"
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
  - "learnloop.figures.request module"
  - "src/learnloop/figures/request.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.request`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.request` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: A figure request: what may be asked, by whom and from where, and the key its build is admitted under.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py) |
| Source lines | 473 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class FigureRefused(Exception)` ([source](../../../../../../src/learnloop/figures/request.py), line 75) — A request the Reader may not make (``code``: ``figures_disabled``, ``exam_material``, ``region_disabled``, ``revisions_disabled``, ``predictions_disabled``, ``offers_disabled`` and ``advanced_disabled`` (RW5b), ``not_found``, ``validation_error``, ``no_image_input``, ``region_un…
  - `__init__(self, code: str, message: str) -> None` (line 83; internal)
- `class FigureRequest` ([source](../../../../../../src/learnloop/figures/request.py), line 90)
- `attempt_hosted(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/request.py), line 150) — RW5d P3: a request made on an attempt host (practice, feedback or the workbench: its verified host references name an item or attempt).
- `lesson_hosted(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/request.py), line 157) — RW5d P4b: a lesson's visual (origin ``teacher``; its host is the lesson, so it has no reading position and no home: it shows in the lesson only).
- `prediction_home(row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/request.py), line 164) — The extraction a figure's prediction is recorded under: its home, or (RW5d P3, an attempt host's figure with no home) the first book it was grounded in; None for a homeless illustration (its predictions are kept with no extraction: Codex review F9).
- `anchored(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/request.py), line 176) — A request with a passage (a selection or a region).
- `show_me_input(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/request.py), line 182) — RW5d: a request whose goal or grounding the author is sent (a goal, or no passage).
- `build_key(vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/request.py), line 193) — What a build depends on, compared before every request it makes (:class:`~learnloop.figure_admission.FiguresGate`): the vault, the switch, the author route as configured, the day's cap and the price, and (RW5b) whether the advanced panels are on (the author's prompt depends on i…
- `offer_build_key(vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/request.py), line 212) — An offered build's key (origin ``library`` | ``tutor``): :func:`build_key` and ``figures.offers_enabled``, so switching offers off stops it.
- `offered(request: 'FigureRequest') -> bool` ([source](../../../../../../src/learnloop/figures/request.py), line 219) — A build an offer started (a "not right?" version of an offered figure is a revision: ``figures.revisions_enabled`` governs it, not the offers).
- `show_me_build_key(vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/request.py), line 226) — A show-me build's key: :func:`build_key` and ``figures.show_me_enabled``.
- `key_for(request: 'FigureRequest')` ([source](../../../../../../src/learnloop/figures/request.py), line 232)
- `check_request(vault: Any, repository: Repository, request: FigureRequest) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/request.py), line 398) — Validate a request and refuse held-out material, on the request path, before any job or call (the handler's first step; the build repeats it).

### Module constants

- `ORIGINS` ([src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py), line 57)
- `RESERVED_ORIGINS` ([src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py), line 58)
- `SERVICE_ORIGINS` ([src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py), line 60)
- `LESSON_TIERS` ([src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py), line 64)
- `OFFER_ORIGINS` ([src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py), line 66)
- `GOAL_AUTHORS` ([src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py), line 69)
- `GOAL_CHARS` ([src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py), line 70)
- `GROUNDINGS` ([src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py), line 71)
- `NOTE_CHARS` ([src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py), line 72)
- `_PREFETCH_BUILD` ([src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py), line 268)
- `PREFETCH_GOAL_AUTHORS` ([src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py), line 270)

### Explicit exports

`__all__` declares:

- `FigureRefused`
- `FigureRequest`
- `GOAL_AUTHORS`
- `GOAL_CHARS`
- `GROUNDINGS`
- `LESSON_TIERS`
- `NOTE_CHARS`
- `OFFER_ORIGINS`
- `ORIGINS`
- `PREFETCH_GOAL_AUTHORS`
- `RESERVED_ORIGINS`
- `SERVICE_ORIGINS`
- `anchored`
- `attempt_hosted`
- `build_key`
- `check_request`
- `key_for`
- `lesson_hosted`
- `offer_build_key`
- `offered`
- `prediction_home`
- `show_me_build_key`
- `show_me_input`

## Internal implementation anchors

- `_key_for(request: 'FigureRequest')` ([source](../../../../../../src/learnloop/figures/request.py), line 254)
- `_validated_request(vault: Any, repository: Repository, request: FigureRequest) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/request.py), line 273)
- `_validated_prefetch(vault: Any, request: FigureRequest) -> FigureRequest` ([source](../../../../../../src/learnloop/figures/request.py), line 362) — RW5d P5: a prefetch build's request, as the prefetch service made it: an anchor (a passage of a book), an optional goal by the prefetch judge or a lesson plan's teacher, never an attempt host, a region or a revision.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]] — imports `FigureRefused`, `FigureRequest`, `_PREFETCH_BUILD`, `anchored`, `attempt_hosted`, `check_request`, `key_for`, `lesson_hosted`, `show_me_input`; statically calls `FigureRefused`, `FigureRequest`, `anchored`, `attempt_hosted`, `check_request`, `key_for`, `lesson_hosted`, `show_me_input`
- [[Reference/Modules/learnloop/figures/grounding|learnloop.figures.grounding]] — imports `FigureRefused`, `FigureRequest`, `anchored`; statically calls `FigureRefused`, `anchored`
- [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]] — imports `FigureRefused`, `FigureRequest`; statically calls `FigureRefused`, `FigureRequest`
- [[Reference/Modules/learnloop/figures/predictions|learnloop.figures.predictions]] — imports `FigureRefused`, `prediction_home`; statically calls `FigureRefused`, `prediction_home`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `FigureRequest`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `FigureRequest`, `module`; statically calls `FigureRequest`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `FigureRequest`, `anchored`, `attempt_hosted`, `check_request`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `figure`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `advanced_panels_enabled`, `author_learner_state_enabled`, `checked_labels_enabled`, `figures_enabled`, `help_kind_enabled`, `offers_enabled`, `region_enabled`, `revisions_enabled`, `rich_tiers_enabled`, `show_me_enabled`, `sketch_enabled`, `teacher_visuals_enabled`; calls `advanced_panels_enabled`, `author_learner_state_enabled`, `checked_labels_enabled`, `figures_enabled`, `help_kind_enabled`, `offers_enabled`, `region_enabled`, `revisions_enabled`, `rich_tiers_enabled`, `show_me_enabled`, `sketch_enabled`, `teacher_visuals_enabled`
- [[Reference/Modules/learnloop/figures/power|learnloop.figures.power]] — imports `prefetch_switch`; calls `prefetch_switch`
- [[Reference/Modules/learnloop/figures/protection|learnloop.figures.protection]] — imports `ATTEMPT_HOST_REFS`, `keys_withheld`, `row_withheld`, `show_me_row`, `withheld_message`; calls `keys_withheld`, `row_withheld`, `show_me_row`, `withheld_message`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `module`; calls `manim_tier_ready`, `rich_tiers_switch`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `module`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `sketch_ready`; calls `sketch_ready`
- [[Reference/Modules/learnloop/figures/view|learnloop.figures.view]] — imports `_advanced_kinds`, `rich_row`, `sketch_row`; calls `_advanced_kinds`, `rich_row`, `sketch_row`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`; calls `plan_route`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]], [[Reference/Modules/learnloop/figures/grounding|learnloop.figures.grounding]], [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]], [[Reference/Modules/learnloop/figures/predictions|learnloop.figures.predictions]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/figure_rich_job_helpers.py](../../../../../../tests/figure_rich_job_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/rw5c_golden_source.py](../../../../../../tests/rw5c_golden_source.py) — direct import
- [tests/test_figure_decision_records.py](../../../../../../tests/test_figure_decision_records.py) — direct import
  - `test_a_refused_build_leaves_a_refused_record`
  - `test_a_refused_or_failed_prebuild_is_a_stop_record`
- [tests/test_figure_label_wording.py](../../../../../../tests/test_figure_label_wording.py) — direct import
  - `test_f3_a_stored_label_like_sketch_is_presented_without_that_text`
  - `test_f3_a_stored_label_like_spec_is_presented_without_that_text_listed_and_reused`
- [tests/test_figure_offers.py](../../../../../../tests/test_figure_offers.py) — direct import
  - `test_a_build_stops_when_the_advanced_panels_are_switched_off_mid_build`
  - `test_a_selection_build_does_not_stop_for_the_offers_switch`
  - `test_an_offered_build_stops_when_offers_are_switched_off_before_its_request`
  - `test_offers_off_the_contract_has_none_and_the_press_is_refused`
  - `test_the_gate_key_of_an_offered_build_includes_the_offers_switch`
- [tests/test_figure_rich_contract.py](../../../../../../tests/test_figure_rich_contract.py) — direct import
  - `test_a_build_with_manim_on_the_menu_sends_v3_and_records_the_menu`
  - `test_the_reuse_key_names_the_menu_and_the_rich_versions`
  - `test_v3_a_status_off_the_menu_or_with_no_reason_gets_the_second_attempt`
  - `test_with_no_rich_tier_on_the_menu_the_contract_is_v2s_byte_for_byte`
  - `test_without_a_way_to_start_the_job_no_rich_tier_is_offered`
- [tests/test_figure_rich_job_golden.py](../../../../../../tests/test_figure_rich_job_golden.py) — direct import
- [tests/test_figure_rich_review_fixes.py](../../../../../../tests/test_figure_rich_review_fixes.py) — direct import
  - `test_a_cancelled_rich_only_build_leaves_no_line_and_cannot_be_retried`
  - `test_a_failed_enqueue_is_not_swallowed_and_is_recovered`
  - `test_a_revision_needs_the_manim_tier_on_this_computer`
- [tests/test_figure_wait_estimate.py](../../../../../../tests/test_figure_wait_estimate.py) — direct import
- [tests/test_figures_codex_review.py](../../../../../../tests/test_figures_codex_review.py) — direct import
  - `test_f7_a_paid_answer_survives_a_crash_before_the_row`
  - `test_f7_a_stored_failure_is_a_new_generation_that_asks_afresh`
  - `test_f7_identical_concurrent_builds_join_one_build`
- [tests/test_figures_final_round.py](../../../../../../tests/test_figures_final_round.py) — direct import
  - `test_a_provider_that_cannot_isolate_is_refused_before_any_request`
- [tests/test_figures_fix_round2.py](../../../../../../tests/test_figures_fix_round2.py) — direct import
  - `test_f7_a_build_committed_between_the_reads_is_reused_inside_the_lock`
- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_f5_an_attempt_builds_admission_key_carries_the_switch`
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_a_background_build_stops_off_mains_before_any_request`
  - `test_origin_prefetch_is_refused_from_every_rpc_and_outside_the_service`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f2_a_quick_prebuild_on_a_metered_author_route_sends_nothing`
  - `test_f7_a_quick_prebuild_stops_before_its_request_while_the_learner_works`
  - `test_r1_a_pressed_fuller_keeps_its_pending_line_and_is_not_speculative`
- [tests/test_figures_rw5b_review.py](../../../../../../tests/test_figures_rw5b_review.py) — direct import
  - `test_the_reuse_key_never_names_the_origin_and_keeps_rw5as_keys`
- [tests/test_figures_scope_redesign.py](../../../../../../tests/test_figures_scope_redesign.py) — direct import
  - `test_a_build_makes_no_request_after_its_configuration_changes`
  - `test_the_build_control_makes_every_request`
- [tests/test_figures_show_me_codex_review.py](../../../../../../tests/test_figures_show_me_codex_review.py) — direct import
  - `test_f1_a_reuse_after_show_me_is_switched_off_is_refused`
  - `test_f1_switching_off_during_grounding_stops_its_calls_and_the_author`
  - `test_f1_the_control_admits_every_grounding_call`
- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — direct import
  - `test_e_the_visual_builder_decides_by_the_lesson_gate_alone`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
  - `test_a_figure_the_learner_pressed_for_meanwhile_is_not_counted_as_the_prebuilds`
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_switched_off_the_payload_prompt_and_key_are_the_predecessors_byte_for_byte`
  - `test_the_learner_state_reaches_the_author_and_protected_work_never_does`
  - `test_the_reuse_key_and_prompt_version_name_the_state_only_when_non_empty`
  - `test_the_rich_author_receives_what_the_figure_author_received`
  - `test_the_switch_is_in_the_build_and_rich_keys`
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_a_visual_turn_builds_a_teacher_figure_shown_inline_with_its_predictions_suppressed`
  - `test_switching_visuals_off_hides_a_lessons_figures_and_stops_a_pending_one`
  - `test_the_teacher_origin_is_the_lesson_services_only`
- [tests/test_rw5c_judgments.py](../../../../../../tests/test_rw5c_judgments.py) — direct import
  - `test_at_build_a_failure_leaves_no_figure_row_and_no_verdict`
- [tests/test_rw5c_recheck.py](../../../../../../tests/test_rw5c_recheck.py) — direct import
  - `test_a_difference_found_at_recheck_gives_the_failed_state_with_rebuild`
  - `test_a_prebuilt_figure_nobody_pressed_for_that_differs_lists_nothing`
  - `test_the_reuse_key_is_unchanged_without_a_source_check_id`
- [tests/test_rw5c_source_check.py](../../../../../../tests/test_rw5c_source_check.py) — direct import
  - `test_build_key_holds_the_switch_and_the_reuse_key_does_not`
  - `test_the_switch_off_at_the_store_writes_nothing`
  - `test_the_switch_off_between_the_sandbox_and_the_second_attempt_stops_the_build`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_off_the_contract_prompt_and_key_are_rw5bs_byte_for_byte`

## Modification guidance

- Make changes here when the responsibility remains request within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/request.py](../../../../../../src/learnloop/figures/request.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
