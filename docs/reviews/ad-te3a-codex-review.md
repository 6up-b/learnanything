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

## Re-review

Codex re-review job `20261106-060104-TXdkLs` on `14aec49e17`: verdict REOPENED. F1 was reopened, F2 and F3 were
confirmed fixed, and no new defect was found. No model request is added (0 paid calls a day; no paid call was made by
this step). No migration, schema, config key, decision constant or frontend change. No reader or writer of the old
item difficulty scalar is added.

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 (reopened) | High | Historical item revisions a lesson exposed are not revalidated (only current ids are) | Fixed | `586a9ebbf5` | `test_te3a_lesson_opportunity.py::test_codex_rereview_f1_a_lesson_is_judged_by_the_revision_it_showed_not_the_items_current_one` (fails on the pre-fix code; also fails with the identity rule neutralized), `::test_codex_f1_the_teachers_close_records_each_delivered_passages_reading` (now pins `exposure.identities`) |
| F2 | Medium | The seeded lesson prior changes decisions | Confirmed fixed by Codex (no change) | `92b69287ef` | n/a |
| F3 | Medium | Rollouts never advance or reset the lesson window | Confirmed fixed by Codex (no change) | `92b69287ef` | n/a |

### F1 (reopened): what was wrong, what changed

Reproduced on a synthetic vault (`ad23_vault`, fakes only): a receipt showed `pi_l1`. The revision it showed cites
block `ext_old/b1`, and the item's current revision cites nothing protected. Then `ext_old/b1` became held out (the
predicate's `held_out_material` patched, as in `test_ad_epoch.py`). The item's current id was still visible
(`pi_l1 not in Protection.ids`), and the receipt carried no revision identity, so the pre-fix rule kept the lesson.
A receipt naming an exposed item with no identity was also admitted.

* `teacher/service._receipt`: `exposure.identities`. For each exposed item (revealed or shown) that is still in the
  vault at the close, in id order, it records `{practice_item_id, keys, whole}`: the block keys and whole
  extractions that the revision's canonical exercise and provenance refs cite (`exam_material.item_source_keys`; ids,
  no text). This is the shape of AD's `outside.source_identity`, and a test pins the two equal.
* `material_view._lesson_exposure` / `_lesson_record_withheld`: every identity is revalidated against today's
  protection by `Protection.covers_identity`. That is the same frozen-revision rule the AD serve uses (Codex
  re-review F11 of AD23). A revision protected after its item got a public replacement therefore still withholds the
  lesson. The rule also withholds a receipt (fail closed) when it names an exposed item without an identity (closed
  before this change, or the item was gone from the vault at the close), when it has a malformed identity list, or
  when the predicate is unavailable. Protection that changes moves the epoch, so the sweep at the new epoch
  re-resolves each receipt by this rule, and the replay reads only what that sweep recorded (the test checks the
  replay after the change).
* Residual, recorded in `teacher-te3a.md`: the identity is the revision current at the close. An item edited while
  its lesson was still open is judged by its closing revision. The smallest way to finish: record each reveal's
  identity on that turn's reveal rows and take their union at the close. A lesson lasts minutes, so under the
  proportionate protection bar this is left for later. Receipts closed before TE3a are withheld, as with F1's legacy
  passages; the owner's census had no lesson at the build.
* Docs: spec_teacher_v1 §20 "As built" and the build record's Option B row and "not built" note name the identity
  rule. The module references were regenerated (stamp-only churn left out).

### Gate (re-review step)

Every pytest ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at `-n 6` or serial, one
run at a time. Scripts ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. With no
migration, schema, frontend or Rust change, the durability lane, DB reference scripts, npm, vitest and cargo were not
needed.

* `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0`: done.
* `uv run lint-imports --no-cache`: **43 kept, 0 broken**.
* One targeted run at `-n 6`, **9946 passed** (0 failed), over these files:
  * the stage: `test_te3a_*.py`;
  * the teacher: every `test_teacher_*.py`;
  * AD's guard and material view: `test_ad23_contract.py`, `test_ad23_fix_r7.py`, `test_ad23_fix_r8.py`,
    `test_ad23_fix_r9.py`, `test_ad23_fix_review.py`, `test_ad23_inversion.py`, `test_ad2_serving.py`,
    `test_ad3_subject_view.py`, `test_ad_epoch.py`, `test_ad_guard.py`, `test_ad_guard_offer_receipts.py`,
    `test_ad_guard_reachable_reads.py`, `test_ad_projection.py`, `test_ad_protected_readings.py`,
    `test_ad_protected_tables.py`, `test_ro2_ad_raw_document_reads.py`, `test_ro2_history_protection.py`,
    `test_salience_firewall.py`;
  * every other test file that reads lesson receipts: `test_data_capture_a6_delayed_pick.py`,
    `test_followups_batch5_lesson.py`, `test_goal_contracts.py`, `test_intervention_outcomes_replayer.py`,
    `test_library_exercises.py`, `test_reader_ca6_side_by_side.py`, `test_reader_rw5d_p4b_teacher_visuals.py`,
    `test_reader_rw6b_landing.py`, `test_source_first_needs.py`, `test_substrate_cutover.py`,
    `test_ux_phase4_feedback.py`;
  * the contracts: `test_sidecar_measurement.py` (display-label audit), `test_codex_lockdown_round3.py`
    (process-launch allowlist), `test_codex_lockdown_frozen.py`, `test_cli_help_snapshot.py`, `test_architecture.py`,
    `test_table_roles.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`,
    `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`, `test_sidecar_serializer_snapshot.py`,
    `test_config_refactor.py` (config defaults), `test_public_tip_guards.py`, `test_sqlite_file_copies.py`,
    `test_figures_prefetch_boundary.py`. The frozen deferred cycles contract is in `lint-imports` above.
* After a docstring-only edit and the reference regeneration: `test_te3a_lesson_opportunity.py` and
  `test_architecture.py`, **45 passed**.
* References: `module_generate.py`, then `module_validate.py` (**PASS**) and `validate_vault.py` (**passed**).
  Stamp-only churn (the catalog and three package maps) was left out.
* `git diff --check`: clean.

## Final verify and landing ruling R1

Codex final verify job `20261106-062519-P0bT6y` on `7ee764d334`: F2 and F3 CONFIRMED fixed; F1 (High) REOPENED: an
item replaced before the lesson closes was judged by its revision at the close, not the one the learner saw. The
orchestrator's landing ruling R1 fixes the class at the moment of exposure, with no further Codex round on it (the
orchestrator reads the diff before landing). No model request, migration, schema, config key or decision constant is
added; no reader or writer of the old item difficulty scalar.

| Id | Severity | Title | Verdict | Test |
|---|---|---|---|---|
| F1 (final verify) | High | An item replaced before the close is judged by its close-time revision | Fixed (R1) | `test_te3a_lesson_opportunity.py::test_landing_r1_an_item_replaced_before_the_close_is_judged_by_the_revision_the_lesson_revealed` (fails on `7ee764d334`: the receipt holds only the public revision's identity), `::test_landing_r1_the_receipt_unions_frozen_identities_and_a_display_without_them_fails_closed` |

### F1 (final verify): what was wrong, what changed

Reproduced through the real teacher (`teacher_fakes`, fakes only), following Codex's sequence: an accepted teaching
turn reveals `pi_eig_1` (a `tutor_answer` reveal row) while its revision cites `ext_old/b1`; the item is rewritten
with a public revision before the close; the lesson closes; `ext_old/b1` becomes held out. On `7ee764d334` the
receipt's `exposure.identities` held only `{pi_eig_1, keys: [], whole: []}` (the close-time revision), so AD's
guarded reader admitted the receipt.

* `teacher/service._record_reveals` (the reveal/show write) now returns the frozen identities
  (`_exposed_identities`, AD's `outside.source_identity` shape, ids only) of what that display exposes, as the vault
  holds it at that moment: every item it reveals (a positive `tutor_answer` or `source_review` amount) and every vault
  item that the lesson's displayed text, this display included, shows (`delayed.shown_vault_items`, the close's
  rule). The caller writes them on the displayed record itself, under `payload.exposure_identities`
  (`EXPOSURE_KEY`): the accepted `teacher_turn`'s payload, or a shown `visual`'s. The reveal rows are written first
  and the record is appended after, in the same transaction, so the turn and its exposure still commit or roll back
  together. The transcript the teacher reads takes only named keys of those payloads, so the prompt is unchanged.
* `teacher/service._receipt` (the exposure block): `identities` comes from `_receipt_identities`: the union of the
  identities frozen on every displayed record and the close's own (the recap's display; each item the close counts
  as exposed, as the vault holds it at the close), deduplicated, in id order; never the close-time one alone. A
  displayed record with no frozen identities (a turn shown before this rule) leaves `identities` out, so AD reads
  every exposed item as unidentified and withholds the receipt (fail closed).
* `material_view` is unchanged in behaviour: every identity is still checked with `Protection.covers_identity`, and a
  missing or malformed identity still withholds (docstring updated).
* The change stays inside the reveal/show write and the receipt's exposure block, so TE2's edits to
  `teacher/service.py` should merge beside it.
* Docs: `teacher-te3a.md` (the residual note now records the fix) and spec_teacher_v1 §20 "As built" name the
  frozen-at-exposure rule. Module references were regenerated for the two changed modules (stamp-only churn left
  out).

### Gate (R1 step)

* `uv run lint-imports --no-cache`: **43 kept, 0 broken**.
* Targeted run at `-n 6`, **9142 passed** (0 failed): `test_te3a_*.py`, every `test_teacher_*.py`, AD's guard and
  material-view tests (`test_ad_guard*.py`, `test_ad1_send_guard.py`, `test_ad_protected_tables.py`,
  `test_ad_protected_readings.py`, `test_ad_projection.py`, `test_ad_epoch.py`, `test_ad23_contract.py`,
  `test_ad23_fix_r7.py`, `test_ad23_fix_r8.py`, `test_ad23_fix_r9.py`, `test_ad23_fix_review.py`,
  `test_ad23_inversion.py`, `test_ad2_serving.py`, `test_ad3_subject_view.py`, `test_reader_source_identity_guard.py`,
  `test_ro2_history_protection.py`), `test_salience_firewall.py`, `test_ro2_ad_raw_document_reads.py`.
* The other lesson-receipt and figure readers plus `test_architecture.py`, **363 passed**:
  `test_data_capture_a6_delayed_pick.py`, `test_followups_batch5_lesson.py`, `test_intervention_outcomes_replayer.py`,
  `test_reader_rw5d_p4b_teacher_visuals.py`, `test_reader_rw6b_landing.py`, `test_reader_ca6_side_by_side.py`,
  `test_goal_contracts.py`, `test_library_exercises.py`, `test_source_first_needs.py`, `test_substrate_cutover.py`,
  `test_ux_phase4_feedback.py`.
* One transient failure while iterating: `test_a_lesson_raises_the_prediction_and_never_evidence_or_mastery` failed
  once in a whole-file run (the on and off vaults' recall states differed slightly). It then passed alone 3 times and
  in 3 more whole-file runs. It builds its own `ad23_vault`s and never reaches the code changed here.
* `module_validate.py`: **PASS**. `git diff --check`: clean.
