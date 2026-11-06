# Teacher TE3a: AD's lesson opportunity and the objective's lesson effect (`ad/te3a-lesson-opportunity`, base `5565bede25`)

Built from `docs/specs/spec_teacher_v1.md` revision 5: §24's TE3a row (the scope), §14.2, §23.1 item 4 (owner, Nov 5:
build now, no AD trigger, prior centred on RO4's placeholder) and Q5's amendment to `spec_adaptive_difficulty_v1.md`
A12 limit 1 and D20 (recorded in that spec at this stage: Status, A12, §5.5's row, §5.11's "Lessons", D20). One AD
successor (`mvp-0.50` here, expected `mvp-0.52` at landing: one constant), one migration (248, renumbered at landing
if TE2's lands first). **No model request is added** (0 paid calls a day; no paid call was made by this stage). No
reader or writer of the old item difficulty scalar is added.

## Commits

| Part | Commit | What |
|---|---|---|
| 1 | `27db6a914b` | Migration 248 (`ad_reading_opportunities`' kind CHECK gains `'lesson'`), head fixture `migration_head_248`, head pins |
| 2 | `c884cbfd9c` | The AD successor, its switch, upgrade, defaults snapshots, CLI and openers; version pins |
| 3 | `04d1b40e19` | The lesson opportunity: priors, firewall, `View.reading`'s gate, the sweep, the guard's tables, replay, readiness's `lesson_curve`, the objective's `LESSON` branch, the report |
| 4 | (last) | Spec §20 "As built", the AD spec's amendment, this file, the regenerated references |

## What exists now

| Spec (§14.2) | Where |
|---|---|
| Kind and subkinds | `ad_reading_opportunities.kind = 'lesson'`, subkind `landed` / `taught` (migration 248) |
| Firewall allowlist | `attempts/salience_firewall.py`: `("lesson", landed|taught, "lesson_receipts")`; `LEARNING_OPPORTUNITY_KINDS` gains `lesson`, `READING_OPPORTUNITY_KINDS` names the four reading kinds; the rule text names Q5's amendment |
| The sweep | `adaptive_difficulty/lessons.py` (`lesson_events`), called from `reading.sweep` at the tag with the switch on: one row per closed lesson's node with a vault LO and final status `landed`/`taught`; source `lesson_receipts`, `<lesson id>/<node id>`; source time the receipt's `created_at`; dose 1 on each of the LO's facets; key `lesson:<lesson>/<node>:<lo>`; every unrecorded receipt, however old |
| Priors version | `adaptive_difficulty/priors.py`: `ad_lesson_priors_v1` (`LESSON_PRIORS`, derived; below), separate from `ad_priors_v1` |
| `View.reading` gate | `state.View.reading(..., subkind=)`: `lesson` behind `lessons_on`, each subkind's own coefficients `lesson:<subkind>:<m>` on one lesson window per facet; `_reading_transition` refactored into `_dose_transition` (reading's arithmetic and coefficient order unchanged) |
| Lazy coordinates | `model.Bank.ensure_lessons`: the four coefficients are created at the first lesson opportunity, so a bank no lesson reached has its predecessor's coordinates, hashes and rows exactly |
| Replay | `replay.ReplaySettings.lessons` (from `successor.lesson_opportunities_on`); off, `load_events` reads no lesson row (no transition, no warmth, no fingerprint change); `run` routes a lesson to `View.reading` and keeps it out of the reading split (`after_lesson` is its own); `ad_state` rows name `lesson_priors` only with lessons on |
| Guard tables | `protected_tables`: `lessons`, `lesson_plans`, `lesson_receipts` DENIED → PROTECTED and READING, with `COLUMNS` (a lesson by its own rule over `goal_json`; plan and receipt by their lesson and their own record; `lessons.goal_text` DERIVED, "unread"); the reference kind `lesson`; `column_classes` unchanged (records stay content, read by the rules only), comment updated; checks, turns, payloads and the weight tables stay DENIED |
| Option B | `MaterialView._lesson_record_withheld`: a lesson record naming any reading the withheld material touches (via `exam_material.reference_keys`, so a Reader selection's goal above all, and the receipt's `exposure.readings`) is withheld; since Codex review F1 also a receipt whose shown or revealed item is withheld now, or that names passages without their readings; an unreadable record is withheld; `_opportunity_withheld` resolves a lesson receipt by `lesson_id` |
| Switch off everywhere | `MaterialView.reading_opportunities` hands out no lesson row while the switch is off (the serve's warmth, the sweep's window, the history resolver), and the full-history card drops them too (`history_card.build_sections`) |
| Objective | `readiness.decision_state_fields(learning_moments=True)` returns `lesson_curve` (the `landed` curve's mixture mean and 2x2 covariance; its seeded prior while no lesson reached the bank; each LO's lesson-window position) at the tag with the switch on; `daily_plan.objective_inputs._learning` turns it into `value.LessonCurve` (fitted models only; RO4's priors keep the placeholder); `value.py`'s `LESSON` branch (since Codex review F2, F3): the placeholder, plus, when the curve is present, its learned shift from the seeded prior (`LessonCurve.deviation`) at the topic's lesson-window position, the window carried in the rollout state; `sources["lesson_curve"]` in the trace's sources when present |
| Report | `arms.NOLESSON` (`ad_threshold@subject:nolesson`, run only with lessons on), `Record.after_lesson`, the `lessons_worse_than_no_lessons` auto-flag (recommends `lesson_opportunities = false`; `monitoring.FLAG_SWITCHES`), the dose-and-burden `lesson` row (`dose_report.lesson_row`) and its lines; all absent with the switch off (the report is the predecessor's) |
| Successor | `LESSON_OPPORTUNITY_ALGORITHM_VERSION`, `learnloop.lesson_opportunity_upgrade`, `[adaptive_difficulty] lesson_opportunities` (default true), every defaults snapshot recomputed |

## The prior, and one deviation from §14.2's wording

§14.2 asks for two things of the prior: "centred so that one landed dose moves the LO's predicted success by what RO4's
placeholder assumes" and "widths follow AD's existing rule for a new kind's prior"; §24 asks that "at the seeded prior
the objective's lesson Q̄ equals RO4's placeholder within float tolerance". AD's rule for a new kind (a reading kind's
`γ̄_m + δ_{κ,m}`: means 0.10 and 0.20, variances 0.0098 and 0.02) gives a first dose sd of 0.070 logit; the
placeholder's spread is `γ`'s prior sd times the mass, 0.05. With 0.070 the objective's lesson value at the prior is
not the placeholder's (the second moment differs), so the two clauses cannot both hold. **Built:** the rule's *shape*
(the ratios between the two scales of the means, 0.10 : 0.20, and of the variances, 0.0098 : 0.02) scaled so the first
dose's mean is 0.1 and its sd 0.05: `N(0.0931, 0.0708²)` on the fast scale and `N(0.1861, 0.1011²)` on the slow, the
same for `taught` (`priors._lesson_priors`, computed from `GAMMA_PRIOR`, `LESSON_CHECK_MASS_PRIOR`, `READING_PRIORS`
and `DOSE_SCALES`; no new number). The resulting coefficient widths happen to be the shared reading curve's own
(0.07 and 0.10). The lesson-check mass prior 0.5 is the teacher's seeded mass (`σ(η₀)`, η₀'s prior mean 0, basis
legacy); AD imports nothing of the evidence side, so a test pins `priors.LESSON_CHECK_MASS_PRIOR` to it.

**The draw (revised at Codex review F2, F3; `docs/reviews/ad-te3a-codex-review.md`).** The first build drew the step
as the curve's own mean + sd·z, which equals the placeholder only at `γ`'s *prior*, mass 0.5 and position 0. The
`LESSON` branch is now RO4's placeholder (`θ_γ·mass` on the draw, `γ̄·mass` on the belief, at `γ` as the decision read
it, fitted or not, and the lesson's learned mass) plus what lessons taught the curve beyond its seeded prior, one dose
at the topic's place on its lesson window: the mean shift `Σ_m b_m'(n)(μ_m − μ⁰_m)` on both, and the step's variance
change `s(n)ᵀ(Σ − Σ⁰)s(n)` on the draw's spread along `γ`'s stream. Both are exactly zero at the prior, so the lesson
is the placeholder draw for draw at any `γ`, mass or position, and the window is carried through the rollout (a
lesson advances it; practice, the tail's batch and a probe reset it). At the seeded prior two consecutive lessons on
one topic therefore add the placeholder's 0.2, not AD's two-dose 0.154: the spec's "switching TE3a on moves no
decision until data arrive" (§14.2, the owner's §23.1 item 4) rules there; the learned shift follows AD's window.

**One dose per node, on every facet of the LO.** §5.11's reading rule spreads an LO-only opportunity's dose 1 over the
LO's facets; a lesson names its LO's facets directly (dose 1 each), so one landed dose moves the LO's `η` by one curve
step whatever its facet count (the centring holds for every LO, and the objective's per-LO step is the same number).

## Numbers on a synthetic vault (fakes only)

The `ad23` plan vault at `mvp-0.50` (3 items on `lo_m1`, facet `recall`), a closed lesson `les_a` with nodes landed,
taught, held, uncertain and one on an LO not in the vault; one backfill sweep; then three answers (right, wrong,
right) on the fakes' clock. Script: `scratchpad/ad-te3a/scripts/te3a_review_numbers.py` (outside the checkout).

**Recorded opportunities:** exactly two, `les_a/n1` (landed) and `les_a/n2` (taught), source time the receipt's
(`2026-10-11T10:00:00Z`), doses `{"recall": 1.0}`; held, uncertain and the unknown LO wrote nothing; a second sweep
wrote nothing.

**The lesson row at the prior** (no lesson): per subkind, first dose median **+0.101 logit** (90% interval +0.015 to
+0.175; 400 seeded draws), **+1.5 points** at the band's centre (+0.2 to +2.5); RO4's placeholder beside it 0.100.
Lines: "A lesson (landed): about +1.5 points on your next cold answer on its topic (90% interval +0.2 to +2.5; 0
lesson node(s); your prior: no lesson followed by a cold answer yet)." The curve's median at n = 1, 2, 3, 10 lessons
in one window: 0.101, 0.153, 0.183, 0.253.

**After the lesson and the answers:** posterior `lesson:landed` means (0.0936, 0.1865) against the prior (0.0931,
0.1861), variances barely contracted (one informative first attempt, `after_lesson` n = 1, realized 1.0, predicted
0.387 with lessons against 0.363 without); row: landed +0.096 logit (+1.4 points, +0.2 to +2.6), taught +0.097;
the flag `lessons_worse_than_no_lessons` does not fire (n = 1, sequence [-0.71, +0.58]).

**Replay equivalence:** live snapshot `5bbe79e99d741a43` = fresh replay of the receipts `5bbe79e99d741a43`; the
rebuild's `ad_state` subject summary hash = the fresh subject bank's (`09d3386289ab2f4c`); the same vault read with
lessons off (`df264c5dc8f8b7f9`) equals a replay of the events with the lesson rows removed, and the bank has no
lesson coordinate; a vault that never had a lesson has the same subject bank hash with the switch on and off and the
same coordinates as at `mvp-0.49` (`tests/test_te3a_lesson_opportunity.py`).

**The objective's lesson Q̄ against RO4's placeholder** (two topics, an exam in 6 days, 64 draws, a lesson on both
topics at mass 0.5; recomputed after Codex review F2, F3 by `scratchpad/ad-te3a/fix/scripts/review_numbers.py`): at
the seeded prior the curve's Q̄ equals the placeholder's exactly, at `γ`'s prior (**0.2342127957735361** both), at the
vault's fitted `γ` (0.19979, 0.00996: **0.23413775813625765** both) and at F2's `γ` (0.05, 0.01: **0.07115061473999681**
both), with positions 0 or (2, 1); largest per-draw difference **0.0**. After the lesson above the curve the objective
reads is the posterior (means 0.09356, 0.18649 against the prior's 0.09306, 0.18613; position 0 after the answers
closed the window): its learned first-dose shift is +0.00039 logit, and Q̄ is 0.23417199 against the placeholder's
0.23413776 at the same fitted `γ`: the learned shift, not the prior, moves it, by 3.4e-5.

## AD's eta growth (the router follow-ups' finding), and the lesson curve

Not changed here. AD's practice transition adds `γ·w` to a cell per eligible practice opportunity, linearly and
without saturation or mean decay (drift adds variance only), so on a 180-day probe `η` reaches about 42 logits. How
the lesson opportunity interacts with it:

* **Within a window the lesson curve saturates** (`b_m(n) = 1 − e^(−n/h_m)`): a window's whole lesson effect is
  bounded by `|c_1| + |c_2|` (about 0.28 logit at the prior). **Across windows it does not:** each graded attempt
  closes the window, so the next lesson starts again at n = 0 and adds a full first step (0.1 at the prior). Over many
  lesson-then-answer cycles the lesson's contribution is linear in the number of lessons, like `γ`'s in the number
  of practices; at one lesson a day it is about a tenth of a logit a day at the prior, small beside practice's
  `γ` per answer but of the same unbounded form. The curve's coefficients and the subject view's facet offsets carry
  no mean decay either.
* **The centring ties AD's lesson prior to `γ`'s prior; the objective follows `γ`'s posterior.** Since Codex review
  F2 the objective values a lesson as RO4's placeholder (`γ`'s posterior times the mass) plus the curve's learned
  shift, so if the unbounded practice growth pushes `γ`'s posterior up, the objective's lesson value follows it, as
  RO4's did, until lessons and later cold answers move the curve off its prior. AD's own lesson prediction (the
  curve in the subject view) stays at its prior scale.
* **What the curve learns from is the same misspecified filter.** A post-lesson cold answer updates the lesson
  coefficients through the facet's covariance with them; any part of the answer the linear `γ` growth over- or
  under-predicts is shared between `γ`, the facet offset and the lesson coefficients in proportion to their
  covariances. Fixing `γ`'s growth (a saturating or decaying practice transition, the follow-ups' recommendation for
  AD) would move the lesson curve's posterior with it; its prior (derived from `γ`'s prior) would then be re-derived
  with the new transition's first-step effect, one line in `priors._lesson_priors`.

## The §24 tests

| Test (§24 TE3a) | Where |
|---|---|
| The AD guard refuses unclassified reads and fails closed | `test_te3a_lesson_opportunity.py::test_the_guard_refuses_raw_and_unclassified_reads_of_lesson_tables` (a raw read of `lesson_receipts` or `lesson_checks` inside an operation is refused and poisons it; the rules read it; an unclassified table is refused); `::test_a_lesson_naming_a_withheld_reading_is_absent_and_an_unavailable_predicate_reads_none`; `test_ad_protected_tables.py` (every column classified, every derived column treated, READING ⊆ COLUMNS); `test_ro2_ad_raw_document_reads.py`'s walk now roots at `lessons.py`, `value.py`, `dose_report.py` and the upgrade |
| Replay equivalence | `::test_replay_equivalence_live_fresh_and_rebuilt` |
| Switch off is AD's predecessor and RO4's placeholder exactly | `::test_switch_off_is_the_predecessor_exactly`, `::test_switch_off_or_below_the_tag_records_nothing`, `::test_the_view_gate_applies_each_subkinds_curve_and_off_is_the_predecessor_exactly`, `::test_the_objective_reads_the_curve_through_ads_entry_only_at_the_tag_with_the_switch_on` (off / below the tag / fitted models off: `Learning.lesson is None`, the placeholder) |
| At the seeded prior the lesson Q̄ equals the placeholder | `::test_at_the_seeded_prior_the_lesson_q_bar_equals_ro4s_placeholder` (1e-12, and draw for draw), `::test_codex_f2_with_fitted_practice_parameters_the_untouched_lesson_curve_moves_no_decision` (fitted `γ`, two masses, two positions: equal draw for draw), `::test_codex_f3_rollouts_carry_the_lesson_window_as_ads_transition_does` (sequences against AD's transition) |
| AD never writes evidence or mastery | `::test_the_import_linter_contract_keeps_ad_off_evidence_writers` (the `adaptive-difficulty-never-writes-evidence` contract, no TE3a exception) and `lint-imports` (43 kept); `::test_a_lesson_raises_the_prediction_and_never_evidence_or_mastery` (the evidence tables byte-identical on vs off) |
| The report's lesson row | `::test_the_reports_lesson_row_at_the_prior_and_after_lessons` |
| The firewall's allowlist | `test_salience_firewall.py` (the listed set gains the two lesson sources; every other table refused), `::test_the_firewall_admits_exactly_the_lesson_subkinds_and_they_stay_salience_only` |
| The successor | `test_te3a_successor.py` |
| The migration | `test_te3a_migration.py` |

## Not built, or built differently (with the smallest way to finish)

* **The readings a lesson's book used: built at Codex review F1.** The receipt gains `exposure.readings`
  (`{alias, extraction_id, span_id}` per delivered passage, ids only; `teacher/service._receipt`, one key, which TE2's
  landing may need to merge beside its own receipt edits); AD's rule reads it as any named reading. A receipt with
  passages and no `readings` (closed before TE3a) cannot be judged and is withheld.
* **"A graded lesson check takes the kind's increment in place of γ."** AD's eligibility admits no lesson check
  (§14.1: `reconstruction_after_walkthrough` is not an eligible type), so no `γ` is applied to one and there is
  nothing to replace; the in-passage hook (`in_passage_kind`) stays unwired, as it is for reading.
* **"With availability, RO1's `known_at` / `attempt_time_sql`."** Those predicates are over `practice_attempts`; the
  lesson opportunity reads no attempt. Its availability is the receipt's own write time (written at the close), used
  as the source time and as the sweep's `as_of` cutoff, so a decision before the close never sees the lesson.
* **The lesson row's minutes per lesson.** The burden side (TE2-log's `lesson_activity_intervals`) is DENIED to AD and
  not read; the row reports effect only. Smallest finish: the teacher report (which reads the intervals) shows the
  minutes beside AD's row.
* **The trace's sensors for an offer** (curve version and moments per offer candidate) are TE3b's; TE3a puts the
  curve in the decision's `sources["lesson_curve"]` when present.
* **Patching.** Two mechanical token renames were done with `sed`/a scratch script over the files `git grep` named
  (`migration_head_247` → `248` and the head-number pins; the 40 snapshot hashes; the tests' latest-version pins:
  negative chain indexes, frozensets, the openers' link), each diff reviewed line by line; every other change used
  the Edit tool.

## Gate (this step)

Every pytest inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`; ad-hoc scripts under
`env -i` with empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`. No frontend or Rust change (no npm, vitest, cargo).

* `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0`.
* `uv run lint-imports --no-cache`: **43 kept, 0 broken**.
* Migration and head pins: the 68 test files the head rename touched plus `test_te3a_migration.py`: 820 passed, 3
  skipped, 13 failed (the earlier migrations' "alters nothing" diffs), fixed with `TE3A_ALTERED_TABLES`; those 13
  files rerun: **63 passed**. `-m durability` over the AD/teacher/reader migration files, `test_migrations.py`,
  `test_tracked_fixture_databases.py`: **5 passed**; `--durable-sqlite tests/test_te3a_migration.py`: **3 passed**.
* Successor: every test file with a version pin, the defaults snapshot or the registry (75 files), the new successor
  test and the CLI help snapshot: 1430 passed, 12 skipped, 3 xfailed, 7 failed (pins written with
  `LATEST_ALGORITHM_VERSION` in the set, and two openers tests), fixed; the 7 tests plus `test_te3a_lesson_opportunity.py`,
  `test_salience_firewall.py`, `test_ad_protected_tables.py`, `test_teacher_te1_migration.py`,
  `test_ro2_ad_raw_document_reads.py`: **8420 passed** (one TE3a test then failed on wall-clock mastery noise; fixed
  with the fakes' clock: `test_te3a_lesson_opportunity.py` **16 passed**).
* AD and the objective: every test file naming `adaptive_difficulty`, the objective's value, inputs or chooser, the
  firewall or the AD fakes (131 files): 10748 passed, 3 skipped, 36 xfailed, 2 failed (`test_ad3_monitoring.py`'s
  flag set, `test_ad23_sim.py`'s G-AD3-9 over `FLAG_SWITCHES`), fixed; the two files: **25 passed, 36 xfailed**.
* Contracts, teacher and router objective: `test_sidecar_measurement.py` (display label audit),
  `test_codex_lockdown_round3.py` (process launch list), `test_cli_help_snapshot.py`, `test_architecture.py`,
  `test_table_roles.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`,
  `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`, `test_sidecar_serializer_snapshot.py`,
  `test_ad_guard_reachable_reads.py`, `test_ro1_availability_reads.py`, `test_public_tip_guards.py`,
  `test_registry_audit.py`, `test_sqlite_file_copies.py`, every `test_teacher_*.py` and `test_ro[0-9]*.py`: **1257
  passed**. The frozen cycles are import-linter's contract (kept).
* References: `db_generate_reference.py` then `db_validate_reference.py` (pass, after the two prose leaf counts
  1171 → 1172), `module_generate.py` then `module_validate.py` (pass), `validate_vault.py` (pass); stamp-only churn
  (source commit lines alone) left out.

The full suite, the durability lane and vitest run once at landing.

## Owner actions

None new. At landing: renumber `mvp-0.50` and migration 248 if the router follow-ups or TE2 claimed them, rebuild the
head fixture from main's head, and move the version pins. After landing, the owner's vault upgrade to the chain's head
activates it; the census has no lesson, so the curve stays at its prior and the objective values a lesson exactly as
RO4 does until lessons and later cold answers exist.
