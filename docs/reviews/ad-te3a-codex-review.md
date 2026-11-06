# TE3a Codex review (gpt-6.1-sol): findings and fixes (`ad/te3a-lesson-opportunity`)

Review job `20261106-050750-WnOA7Y` on `508870e9a6`. Three findings, all reproduced, all fixed. The build record is
`docs/reviews/teacher-te3a.md` (its prior, draw, numbers and "not built" sections are updated for these fixes). No
model request is added (0 paid calls a day; no paid call made by this step). No reader or writer of the old item
difficulty scalar is added; no migration, no new config key, no new decision constant.

## Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Protected item exposures survive the lesson protection filter | Fixed | `450a72924e` | `test_te3a_lesson_opportunity.py::test_codex_f1_a_lesson_whose_shown_items_or_passages_are_withheld_now_is_absent`, `::test_codex_f1_the_teachers_close_records_each_delivered_passages_reading` (both fail on the pre-fix code) |
| F2 | Medium | The seeded lesson prior changes decisions on an already-trained vault | Fixed | `92b69287ef` | `::test_codex_f2_with_fitted_practice_parameters_the_untouched_lesson_curve_moves_no_decision` (4 cases), `::test_at_the_seeded_prior_the_lesson_q_bar_equals_ro4s_placeholder` (now position-neutral at the prior) |
| F3 | Medium | Rollouts never advance or reset the lesson window | Fixed | `92b69287ef` | `::test_codex_f3_rollouts_carry_the_lesson_window_as_ads_transition_does` (LL, LPL, LBL, LLPL against AD's own `View` transition) |

### F1: what was wrong, what changed

Reproduced: a receipt naming `pi_exam` in `exposure.shown_items` (or `pi_exam_2` in `exposure.reveals`) kept its
recorded `landed` opportunity in the replay after the item became protected, and an alias-only receipt
(`exposure.passages` with no extraction ids) was admitted even though its book could not be judged.

* `material_view._lesson_exposure` / `_lesson_record_withheld`: a receipt is withheld when an item it showed or
  revealed is withheld now (`MaterialView.withheld`, today's protection; the receipt names item ids only, no
  revision), or when it names passages without their readings (fail closed). Recorded opportunities re-resolve
  their receipt by this rule on every replay, so protection that changes after the close takes effect.
* `teacher/service._receipt`: `exposure.readings`, `{alias, extraction_id, span_id}` per delivered passage (ids, no
  text). AD's reference rule (`exam_material.reference_keys`) reads it as any named reading, so Option B now covers
  the lesson's book. This is one key in `_receipt`; TE2 (building in parallel) also edits `teacher/service.py`, so
  its landing may need a trivial merge at that dict.
* Legacy receipts with passages and no `readings` are withheld from AD. The owner's census had no lesson at the
  build, so this drops nothing real; a lesson closed after landing carries its readings.

### F2: what was wrong, what changed

Reproduced (`scratchpad/ad-te3a/fix/scripts/repro_f2_f3.py`, practised topics, one-minute lesson and practice on
`lo_a`, `γ` fitted at (0.05, 0.01), lesson curve at its seeded prior): pre-fix lesson Q̄ **0.130297** with the curve
against **0.117735** with RO4's placeholder (practice 0.106346): the untouched curve moved the lesson's value (in
Codex's inputs it flipped the choice). After the fix both are **0.11773467769516029**, draw for draw.

* `value.LessonCurve` carries its seeded prior (`prior_mean`, `prior_cov`, from `readiness.lesson_curve_moments`,
  passed by `objective_inputs._lesson_curve` and named in the trace's `sources["lesson_curve"]`).
* The `LESSON` branch is RO4's placeholder (`θ_γ·mass` on the draw, `γ̄·mass` on the belief, at the decision's `γ`,
  fitted or prior, and the lesson's learned mass) plus `LessonCurve.deviation`: the dose's mean shift
  `Σ_m b_m'(n)(μ_m − μ⁰_m)` on both, and its variance change `s(n)ᵀ(Σ − Σ⁰)s(n)` on the draw's spread along `γ`'s
  stream (`sqrt(base + Δv) − sqrt(base)`). Both are exactly 0.0 at the prior, so the placeholder holds bit for bit
  at any `γ`, mass and position. No sample gate: the first lesson that informs the curve moves it.
* `readiness.lesson_curve_moments`: a bank whose every component still holds the seeded coefficients reports the
  prior exactly (the moment sums would otherwise round it by an ulp after the first lesson, before any answer).

### F3: what was wrong, what changed

Reproduced: with a learned curve (means +0.3, −0.05 off the prior), two consecutive lessons on one topic each added
the first-dose step **0.278576** (the frozen position); after the fix the second adds **0.161150** (AD's second dose
of the learned shift plus the placeholder).

* `_State.lesson` (K × N) carries each topic's lesson window through the rollout (copy and branch select via one
  `_STATE_FIELDS` list), initialized from the curve's positions; a lesson advances it; practice (`_practice`), the
  tail's batch (`_practice_batch`) and a probe (`_observe`) reset it, as every graded attempt closes AD's windows.
* The probe's belief world takes the curve's means only (covariances zeroed with `γ`'s variance).
* The test's oracle is AD's own `View.reading` / `close_windows` on a bank with the learned coefficients minus the
  same on the prior: each lesson step's learned part matches to 1e-12 for LL, LPL, LBL and LLPL.

**Where F3's expected number is not adopted.** Codex compared two lessons at the seeded prior against AD's two-dose
curve (0.153706 logit) rather than the placeholder's 0.2. The spec rules there: §14.2 centres the prior "so that
switching TE3a on moves no decision until data arrive", the owner's §23.1 item 4 accepts that, and the stage's
defect list names "a lesson effect that moves a decision while at its seeded prior". So at the prior the objective is
the placeholder for every sequence (0.2 for two lessons), and the window shapes only what lessons have taught the
curve. F2 and F3's fixes are one parameterization: the learned deviation from the incumbent, on AD's window.

## Claims re-checked

* "At the seeded prior every draw equals the placeholder": now true at fitted `γ`, at masses 0.5 and 0.8, and at
  positions 0, 1, (2, 1) (tests above; numbers below).
* "Protected lesson inputs are revalidated": shown and revealed items and the book's readings now are.
* "The objective uses the same lesson curve as AD": its learned part does, window for window.

## Numbers (synthetic vault, fakes only; `scratchpad/ad-te3a/fix/scripts/review_numbers.py`)

The objective's lesson Q̄ (two topics, exam in 6 days, 64 draws, lesson on both at mass 0.5) at the seeded prior,
placeholder against curve, positions 0 and (2, 1): `γ` prior (0.2, 0.01) **0.2342127957735361** both; the `ad23`
vault's fitted `γ` (0.19979, 0.00996) **0.23413775813625765** both; `γ` (0.05, 0.01) **0.07115061473999681** both;
largest per-draw difference **0.0**. After the build record's lesson and three answers: curve means (0.09356,
0.18649) against the prior's (0.09306, 0.18613), learned first-dose shift +0.00039 logit, Q̄ **0.23417199** against
the placeholder's **0.23413776** (+3.4e-5). The lesson row at the prior and the replay equivalence numbers are
unchanged by these fixes (AD's state and report were not touched; `teacher-te3a.md`'s "Numbers" section).

## Gate (this step)

Every pytest inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run at a
time; scripts under `env -i` with empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`. No migration, schema, config,
frontend or Rust change (no durability lane, DB reference scripts, npm, vitest or cargo needed).

* `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0`: done.
* `uv run lint-imports --no-cache`: **43 kept, 0 broken** (the frozen deferred cycles contract kept).
* While iterating: the F1 set (`test_te3a_lesson_opportunity.py`, the material-view and AD guard tests
  `test_ad23_contract.py`, `test_ad23_fix_r7.py`, `test_ad23_fix_r8.py`, `test_ad23_fix_r9.py`,
  `test_ad23_fix_review.py`, `test_ad23_inversion.py`, `test_ad2_serving.py`, `test_ad3_subject_view.py`,
  `test_ad_epoch.py`, `test_ad_guard.py`, `test_ad_guard_offer_receipts.py`, `test_ad_guard_reachable_reads.py`,
  `test_ad_projection.py`, `test_ad_protected_readings.py`, `test_ad_protected_tables.py`,
  `test_ro2_ad_raw_document_reads.py`, `test_ro2_history_protection.py`, `test_salience_firewall.py`, every
  `test_teacher_*.py`): **9096 passed**. The F2/F3 set (every `test_ro[0-9]*.py`, `test_ad23_contract.py`,
  `test_ad23_fix_r7.py`, `test_ad23_fix_review.py`, `test_ad3_subject_view.py`, `test_mobile_allowlist.py`,
  `test_teacher_te1b_review_fixes.py`, `test_te3a_lesson_opportunity.py`, `test_te3a_successor.py`,
  `test_router_objective_migration.py`, `test_sidecar_serializer_snapshot.py`): **1015 passed**.
* Final run on the finished code, one command: `test_te3a_lesson_opportunity.py` (26), `test_te3a_successor.py`,
  `test_te3a_migration.py`, the AD guard and material-view files above, every `test_ro[0-9]*.py`,
  `test_salience_firewall.py`, every `test_teacher_*.py`, `test_router_objective_migration.py`, and the contracts:
  `test_sidecar_measurement.py` (display-label audit), `test_codex_lockdown_round3.py` (process-launch allowlist),
  `test_codex_lockdown_frozen.py`, `test_cli_help_snapshot.py`, `test_architecture.py`, `test_table_roles.py`,
  `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`, `test_desktop_rpc_contract.py`,
  `test_mobile_allowlist.py`, `test_sidecar_serializer_snapshot.py`, `test_config_refactor.py` (config defaults),
  `test_public_tip_guards.py`, `test_sqlite_file_copies.py`, `test_figures_prefetch_boundary.py`: **10161 passed,
  1 failed**. The failure, `test_ro5_landing.py::test_r8_each_arm_can_be_drawn_with_its_logged_probability_and_no_intervention_serves_no_probe`
  (its `_fg1_env` setup's first served step was not an item, line 412), is at RO5's tag, below TE3a's (lessons off,
  no code path this step touched), passed in the F2/F3 run above, and passes on rerun: alone **1 passed** three
  times, the whole `test_ro5_landing.py` at `-n 6` **22 passed**. Read as a load-dependent flake under the 10k-test
  `-n 6` run; for the landing gate to watch.
* References: `module_generate.py`, then `module_validate.py` (**PASS**) and `validate_vault.py` (**passed**);
  stamp-only churn (five package maps and the catalog's commit timestamps) left out.
* `git diff --check`: clean.
