---
title: "learnloop.figures.view"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/view.py"
source_paths:
  - "src/learnloop/figures/view.py"
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
  - "learnloop.figures.view module"
  - "src/learnloop/figures/view.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.view`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.view` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: How a stored figure is presented now: its row under today's switches, and the view the Reader is sent.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py) |
| Source lines | 774 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `rich_row(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/view.py), line 66) — RW5d P2b: a stored rich figure (a Manim figure).
- `shown_row(row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 76) — The row as RW5a may show it: nothing in RW5a produces "verified", and a stored one (from a build before the owner's scope decision of 2026-10-21) is shown as the illustration RW5a's rules make it.
- `sketch_row(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/view.py), line 106) — RW5d P2: a stored sketch.
- `sketch_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 112) — RW5d P2: a shown sketch where the sealed engine can't run (or figures are off) is the unsupported-kind state ("can't draw this yet"); its program never goes out.
- `rich_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 124) — RW5d P2b: a shown rich figure while ``figures.rich_tiers_enabled`` is off is the unsupported-kind state ("can't show this kind here"); its program and video never go out.
- `reverify_hash(spec_json: str, engine_sha256: str, verifier_version: str | None=None) -> str` ([source](../../../../../../src/learnloop/figures/view.py), line 149)
- `sketch_rechecked(row: Mapping[str, Any], repository: Repository | None=None, *, run: bool=True) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 200) — Spec §8.5, engine upgrades: a shown sketch verified under another engine, or (Codex review F11, round 3) by another verifier version (:data:`.sketch_verify.VERIFIER_REPORT_VERSION`: a report made before a verification fix may carry a check line the fixed verifier would not give)…
- `worded_row(row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 254) — Spec §9b.4 when a stored figure is presented (Reader follow-ups Nov 1b, Codex review F3): a figure stored before the free-text label rule (or by any path that skipped it) is shown, listed and reused without its label-like text, as :mod:`.labels` rules for an answer that still vi…
- `available_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 289) — The chain's first step after :func:`shown_row`: a tier that is off, or that this machine can't run, shown as "can't draw this yet" with its program withheld.
- `drawable_now(vault: Any, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/view.py), line 296) — A stored figure that can be drawn as configured now (:func:`available_row` leaves it as it is).
- `property_checks(report: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/figures/view.py), line 302) — The closed keys of the checks a shown figure passed (§8.3 steps 1-2).
- `figure_view(vault: Any, repository: Repository, row: Mapping[str, Any], *, versions: int=1, home: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 385) — A figure as the Reader shows it.
- `source_rejected(vault: Any, repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/view.py), line 542) — RW5c (§6.6): the figure's newest check, at the current certification version and with the switch on, proved a stated claim different.
- `redelivered_view(vault: Any, repository: Repository, view: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 628) — A figure view kept since its build (a finished job's result, read again through ``reader.figure_job``) as it may go out now (follow-ups Nov 2): its fuller version is rebuilt from the current rows (:func:`fuller_state`), so a fuller version whose learner inputs became protected s…
- `fuller_state(vault: Any, repository: Repository, row: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/view.py), line 663) — RW5d P2b (spec §6.8, §8.6): the fuller version of a quick figure, or None when it has none: ``ready`` (with the rich figure's view), ``failed`` (code's reason; the quick version stays), ``pending`` (the job's phase), ``waiting_for_plan`` or ``cancelled``.

### Module constants

- `NOT_FROM_BOOKS_LABEL` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 47)
- `LEDGER_TASK` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 48)
- `RECONSTRUCTION_REASON` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 51)
- `LABELS` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 54)
- `SKETCH_LABEL` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 58)
- `SKETCH_UNCHECKED_LABEL` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 59)
- `SKETCH_NOT_FROM_BOOKS_LABEL` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 60)
- `SKETCH_OFF_KIND` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 62)
- `ENGINE_CHANGED_REASON` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 63)
- `PROPERTY_CHECKS` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 91)
- `_RECHECKED` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 141)
- `_RECHECKED_GUARD` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 142)
- `REVERIFY_VERSION` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 146)
- `LABEL_CODES` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 318)
- `_CODE_LABELS` ([src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py), line 320)

### Explicit exports

`__all__` declares:

- `ENGINE_CHANGED_REASON`
- `LABELS`
- `LABEL_CODES`
- `LEDGER_TASK`
- `NOT_FROM_BOOKS_LABEL`
- `PROPERTY_CHECKS`
- `RECONSTRUCTION_REASON`
- `REVERIFY_VERSION`
- `SKETCH_LABEL`
- `SKETCH_NOT_FROM_BOOKS_LABEL`
- `SKETCH_OFF_KIND`
- `SKETCH_UNCHECKED_LABEL`
- `available_row`
- `drawable_now`
- `figure_view`
- `fuller_state`
- `property_checks`
- `redelivered_view`
- `reverify_hash`
- `rich_off_row`
- `rich_row`
- `shown_row`
- `sketch_off_row`
- `sketch_rechecked`
- `sketch_row`
- `source_rejected`
- `worded_row`

## Internal implementation anchors

- `_advanced_kinds(row: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/figures/view.py), line 95) — The RW5b panel kinds a stored figure's spec uses (none when it has no spec).
- `_stored_verifier(row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/view.py), line 156) — The verifier report version a stored row's report was made by (None: before the version existed).
- `_record_reverification(repository: Repository | None, row: Mapping[str, Any], cached: Mapping[str, Any], engine_sha256: str) -> None` ([source](../../../../../../src/learnloop/figures/view.py), line 164) — Codex review F8: an engine re-verification is a verifier verdict, so it is appended to ``judgment_ledger`` (task ``figure_verified``, judge ``verifier``) before the figure is delivered, superseding the figure's last verdict on that question.
- `_label_code(row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/view.py), line 329)
- `_label(row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/view.py), line 351)
- `_prediction_view(found: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/view.py), line 362)
- `_anchor_span(row: Mapping[str, Any], asked: Mapping[str, Any] | None, home: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/figures/view.py), line 373) — Where a figure shows: under the selection's last block; a region's figure (no selected text) under the region's block (Codex review F2); RW5d: a figure with no passage under the passage the learner was reading (``home``, else its own request's reading position).
- `_sketch_view(vault: Any, repository: Repository, row: Mapping[str, Any], view: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 467) — A shown sketch as the Reader draws it: the program (its code runs in the desktop's sealed engine), the code-owned check lines and the *not covered* line, and its predictions (answers never sent first).
- `_manim_view(row: Mapping[str, Any], view: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 517) — A shown Manim figure (RW5d P2b, spec §6.8): the content-addressed video (played over ``llmedia://``), its title and transcript, the code-owned check lines and *the video itself is not checked frame by frame*.
- `_source_rejected_row(vault: Any, repository: Repository, row: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 553)
- `_source_check_view(vault: Any, repository: Repository, row: Mapping[str, Any], compiled: S.CompiledFigure, view: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/figures/view.py), line 561) — RW5c (§7.4): a shown grammar figure's ``elements`` and ``source_check``, read from the ledger as the switch is now (absent with it off: the view is RW5a/RW5d's key for key).
- `_coded_answer(answered: Mapping[str, Any], by_label: Mapping[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 592) — An answered area prediction under code-owned labels: its stored answers (shade labels, kept as they were) go out as the shades' element ids.
- `_code_owned_labels(vault: Any, repository: Repository, row: Mapping[str, Any], compiled: S.CompiledFigure) -> dict[str, str] | None` ([source](../../../../../../src/learnloop/figures/view.py), line 600) — Model label -> element id while this figure's labels are code-owned, else None.
- `_presented_row(vault: Any, repository: Repository, row: Mapping[str, Any], *, reverify: bool=True) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/view.py), line 612) — A stored row as :func:`figure_view` presents it under the switches now.
- `_prefetch_intent_refused(vault: Any, repository: Repository, intent: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/view.py), line 716) — Landing ruling R1: whether background admission refuses a prebuild's unqueued rich intent now: figures ahead of need off, this machine not on mains, or its input held out.
- `_figure_request(repository: Repository, row: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/view.py), line 729) — The ``figure_requests`` row a figure was built for (RW5d), or None (RW5a/b rows before 224).
- `_prebuilt_pressed(repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/view.py), line 738)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]] — imports `LEDGER_TASK`, `RECONSTRUCTION_REASON`, `_figure_request`, `drawable_now`, `figure_view`, `rich_row`, `sketch_row`, `source_rejected`; statically calls `_figure_request`, `drawable_now`, `figure_view`, `rich_row`, `sketch_row`, `source_rejected`
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `module`; statically calls `drawable_now`, `rich_row`, `source_rejected`
- [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]] — imports `SKETCH_OFF_KIND`, `_anchor_span`, `_figure_request`, `_label`, `_prebuilt_pressed`, `_presented_row`, `available_row`, `drawable_now`, `figure_view`, `sketch_rechecked`, `sketch_row`, `source_rejected`; statically calls `_anchor_span`, `_figure_request`, `_label`, `_prebuilt_pressed`, `_presented_row`, `available_row`, `drawable_now`, `figure_view`, `sketch_rechecked`, `sketch_row`, `source_rejected`
- [[Reference/Modules/learnloop/figures/predictions|learnloop.figures.predictions]] — imports `_code_owned_labels`, `_coded_answer`, `_prediction_view`; statically calls `_code_owned_labels`, `_coded_answer`, `_prediction_view`
- [[Reference/Modules/learnloop/figures/request|learnloop.figures.request]] — imports `rich_row`, `sketch_row`; statically calls `rich_row`, `sketch_row`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `module`; statically calls `figure_view`, `rich_row`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `figure_view`, `redelivered_view`, `rich_row`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `figure`, `figure_verdicts`, `fuller_rows`, `has_tables`, `predictions_for_figure`, `request`, `shown_verification`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `rich_tiers_enabled`; calls `rich_tiers_enabled`
- [[Reference/Modules/learnloop/figures/elements|learnloop.figures.elements]] — imports `module`; calls `rewrite_spec`
- [[Reference/Modules/learnloop/figures/labels|learnloop.figures.labels]] — imports `module`; calls `label_like`, `strip_json`, `strip_lines`
- [[Reference/Modules/learnloop/figures/power|learnloop.figures.power]] — imports `power_state`, `prefetch_switch`; calls `power_state`, `prefetch_switch`
- [[Reference/Modules/learnloop/figures/protection|learnloop.figures.protection]] — imports `RICH_INTENT_KEY`, `_withheld`, `learner_state_withheld`; calls `_withheld`, `learner_state_withheld`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `module`; calls `job_state`, `rich_job_for_quick`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `module`, `sketch_ready`; calls `parse_sketch`, `sketch_ready`
- [[Reference/Modules/learnloop/figures/sketch_engine|learnloop.figures.sketch_engine]] — imports `ENGINE_SHA256`
- [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]] — imports `VERIFIER_REPORT_VERSION`, `module`; calls `prediction_target_step`, `verify_sketch`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; calls `current_row`, `enabled`, `grammar_row`, `recheck_due`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `RICH_SPEC_VERSIONS`, `module`; calls `advanced_kinds`, `parse_spec`, `prediction_outcome`
- [[Reference/Modules/learnloop/figures/verify|learnloop.figures.verify]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `hashlib`, `json`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]], [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]], [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]], [[Reference/Modules/learnloop/figures/predictions|learnloop.figures.predictions]], [[Reference/Modules/learnloop/figures/request|learnloop.figures.request]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_label_wording.py](../../../../../../tests/test_figure_label_wording.py) — direct import
  - `test_the_vocabulary_comes_from_the_code_owned_labels`
- [tests/test_figure_verification.py](../../../../../../tests/test_figure_verification.py) — direct import
  - `test_g23_holds_vacuously_a_reconstruction_is_an_illustration`
- [tests/test_figure_view_label_codes.py](../../../../../../tests/test_figure_view_label_codes.py) — direct import
  - `test_each_presented_row_has_one_code_and_the_label_follows_it`
  - `test_the_codes_are_closed_and_the_desktop_names_exactly_them`
- [tests/test_figures_final_round.py](../../../../../../tests/test_figures_final_round.py) — direct import
  - `test_the_view_sends_closed_property_check_keys_only`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_r1_a_pressed_fuller_keeps_its_pending_line_and_is_not_speculative`
  - `test_r1_a_queued_speculative_fuller_is_marked_speculative`
  - `test_r1_an_unqueued_speculative_fuller_is_not_pending_on_battery`
  - `test_r1_an_unqueued_speculative_fuller_is_not_pending_switched_off_or_held_out`
- [tests/test_figures_scope_redesign.py](../../../../../../tests/test_figures_scope_redesign.py) — direct import
  - `test_a_stored_verified_row_is_rendered_as_an_illustration`
  - `test_no_figure_is_labelled_checked`
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_a_goal_alone_is_grounded_in_the_books_and_lands_where_the_learner_was`
  - `test_nothing_found_is_built_anyway_as_an_illustration_not_from_your_books`
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_fresh_figure_for_a_marked_row_is_reused_under_another_setting`
- [tests/test_reader_rw5d_p4a_figures_follow.py](../../../../../../tests/test_reader_rw5d_p4a_figures_follow.py) — direct import
  - `test_the_quiet_read_never_reverifies_an_outdated_sketch_or_writes`
- [tests/test_rw5c_labels.py](../../../../../../tests/test_rw5c_labels.py) — direct import
  - `test_a_sketch_view_has_no_elements_or_source_check`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_a_read_without_a_run_honours_only_a_failure_already_found`
  - `test_a_report_from_an_older_verifier_is_reverified_before_it_is_shown`
  - `test_a_report_from_this_verifier_and_engine_is_not_reverified`
  - `test_a_sketch_answer_is_verified_stored_and_shown_with_its_check_lines`
  - `test_a_verifier_version_bump_reverifies_a_current_engines_report`
  - `test_an_engine_reverification_is_a_verifier_judgment_recorded_once`
  - `test_an_engine_upgrade_reverifies_with_no_model_call`

## Modification guidance

- Make changes here when the responsibility remains view within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/view.py](../../../../../../src/learnloop/figures/view.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
