---
title: "learnloop.adaptive_difficulty.readiness"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/readiness.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/readiness.py"
source_commit: "workspace/uncommitted @ HEAD b1c67e1f52ee99dcfab1eeca5de019d636162201"
source_commit_timestamp: "2026-11-06T11:48:24-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.readiness module"
  - "src/learnloop/adaptive_difficulty/readiness.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.readiness`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.readiness` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Readiness numbers from the subject view, and the router card's AD fields (spec §9.5, §10.1, §12).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/readiness.py](../../../../../../src/learnloop/adaptive_difficulty/readiness.py) |
| Source lines | 365 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD b1c67e1f52ee99dcfab1eeca5de019d636162201` |
| Commit timestamp | `2026-11-06T11:48:24-05:00` |

## Public API

- `lo_readiness(vault: Any, repository: Any, learning_object_id: str, *, snapshot: RP.Snapshot | None=None, view: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 58) — The LO's readiness lines (labelled predictions), or the not-predicted line.
- `aggregate_line(rows: list[Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 86) — The LO's one visible line (Codex review F9): "likely ready" only when **every** cell is tested and likely ready; a partly untested LO says so in the line itself, since the desktop shows this line alone, and is never "likely ready" on its tested cells.
- `card_fields(vault: Any, repository: Any, learning_object_id: str, *, snapshot: RP.Snapshot | None=None, view: Any=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 105) — The router card's AD fields for one LO (None with ``promoted_predictor`` off).
- `decision_state_fields(vault: Any, repository: Any, learning_object_ids: Sequence[str], *, snapshot: RP.Snapshot | None=None, view: Any=None, reading_doses: bool=False, learning_moments: bool=False, eta_moments: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 122) — RO0 row 9 (spec_router_objective_v1 §4): the card's numbers for each candidate LO at one decision, and the state they were read from.
- `lesson_curve_moments(subject: Any, subkind: str='landed') -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 179) — Teacher TE3a: a lesson subkind's dose-curve coefficients ``(c_1, c_2)``: the mixture's mean and covariance over the bank's first group (as :func:`_learning_moments`), a read, never a write; the seeded prior (``ad_lesson_priors_v1``) while the bank has no lesson coordinate (no le…
- `band_positions(vault: Any, repository: Any, learning_object_ids: Sequence[str], *, snapshot: RP.Snapshot | None=None, view: Any=None) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 293) — Per LO, where adaptive difficulty predicts the learner stands against its practice band (teacher TE1b's ``below_band`` lesson reason; codex review F6).
- `card_line(fields: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 357)

### Module constants

- `READINESS_VERSION` ([src/learnloop/adaptive_difficulty/readiness.py](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 36)
- `NOT_PREDICTED` ([src/learnloop/adaptive_difficulty/readiness.py](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 37)
- `UNTESTED` ([src/learnloop/adaptive_difficulty/readiness.py](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 38)
- `LIKELY` ([src/learnloop/adaptive_difficulty/readiness.py](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 39)
- `NOT_YET` ([src/learnloop/adaptive_difficulty/readiness.py](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 40)
- `LEARNING_PARAMETERS` ([src/learnloop/adaptive_difficulty/readiness.py](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 214)

### Explicit exports

`__all__` declares:

- `LIKELY`
- `NOT_PREDICTED`
- `NOT_YET`
- `READINESS_VERSION`
- `UNTESTED`
- `aggregate_line`
- `band_positions`
- `card_fields`
- `card_line`
- `decision_state_fields`
- `lesson_curve_moments`
- `lo_readiness`

## Internal implementation anchors

- `_cells(view: Any, learning_object_id: str) -> list[tuple[str, str, str]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 43) — ``(facet, capability, subject)`` of every cell the LO's visible active items measure, read through the material view: a protected item (held-out material, an exam reservation) never shapes a readiness line or the router card (A8); with the predicate unavailable there are none.
- `_learning_moments(subject: Any) -> dict[str, list[float]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 217) — The subject view's posterior mean and variance of ``γ`` and the reading curve's ``γ̄_1, γ̄_2``: the mixture's moments over the bank's first group (``dose_report.coefficient_draws``'s rows), a read, never a write.
- `_lo_fields(vault: Any, view: Any, snapshot: RP.Snapshot, learning_object_id: str, *, moments: bool=False) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 237) — One LO's AD numbers in its main cell, or None with no visible cell.
- `_latent_moments(subject: Any, prediction: PR.Prediction, spec: Any) -> dict[str, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 278) — R10: the latent ``η`` the prediction integrates, as a mixture's mean and variance over the bank's rows (each row's ``(m, v_e)``, weighted as ``predict`` weights them), and the spec's guess.
- `_main_cell(view: Any, vault: Any, learning_object_id: str) -> tuple[str, str, str] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/readiness.py), line 340) — The LO's main cell: the facet its visible items weigh most (as :func:`card_fields` picks).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `decision_state_fields`; statically calls `decision_state_fields`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `band_positions`, `decision_state_fields`; statically calls `band_positions`, `decision_state_fields`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `decision_state_fields`; statically calls `decision_state_fields`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `card_fields`; statically calls `card_fields`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `decision_state_fields`; statically calls `decision_state_fields`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `card_fields`, `lo_readiness`; statically calls `card_fields`, `lo_readiness`
- [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]] — imports `NOT_PREDICTED`, `READINESS_VERSION`, `lo_readiness`; statically calls `lo_readiness`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `LIKELY`, `lo_readiness`; statically calls `lo_readiness`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `decision_state_fields`; statically calls `decision_state_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `decision_state_fields`; statically calls `decision_state_fields`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `module`; calls `capability`, `facet_weights`, `item_subject`, `mixture_weights`, `point_spec`, `predict`, `score`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`; calls `lesson_coordinate`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `snapshot`
- [[Reference/Modules/learnloop/adaptive_difficulty/selection|learnloop.adaptive_difficulty.selection]] — imports `module`; calls `commission_candidates`, `constants_from_config`, `default_target`, `ladder_id`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `lesson_opportunities_on`, `subject_view_live`; calls `lesson_opportunities_on`, `subject_view_live`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_ad23_fix_r7.py](../../../../../../tests/test_ad23_fix_r7.py) — direct import
  - `test_a_protected_item_never_steers_the_commissioned_cell_or_readiness`
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_partly_untested_lo_never_reads_likely_ready`
- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — direct import
  - `test_readiness_numbers_from_subject_view_with_untested_cells`
  - `test_ro0_decision_state_fields_read_the_cards_numbers_with_the_state_they_came_from`
- [tests/test_ro0_codex_review.py](../../../../../../tests/test_ro0_codex_review.py) — direct import
  - `test_f3_a_staged_decision_keeps_its_ad_numbers`
- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f8_ad_reports_the_reading_dose_position_only_when_asked`
- [tests/test_ro5_calibration.py](../../../../../../tests/test_ro5_calibration.py) — direct import
  - `test_ad_exposes_the_subject_views_learning_moments`
- [tests/test_rofu_ad_latent.py](../../../../../../tests/test_rofu_ad_latent.py) — direct import
  - `test_ads_entry_point_hands_the_latent_moments_only_when_asked`
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_after_a_lesson_the_curve_the_objective_reads_has_the_topics_position`
  - `test_the_objective_reads_the_curve_through_ads_entry_only_at_the_tag_with_the_switch_on`
- [tests/test_teacher_te1b_review_fixes.py](../../../../../../tests/test_teacher_te1b_review_fixes.py) — direct import
  - `test_band_positions_thresholds_p_band_and_reads_the_side_from_expected_success`
  - `test_below_band_reads_adaptive_difficultys_posterior_not_the_mastery_model`

## Modification guidance

- Make changes here when the responsibility remains readiness within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/readiness.py](../../../../../../src/learnloop/adaptive_difficulty/readiness.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
