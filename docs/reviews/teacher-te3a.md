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
| Option B | `MaterialView._lesson_record_withheld`: a lesson record naming any reading the withheld material touches (via `exam_material.reference_keys`, so a Reader selection's goal above all, and the receipt's `exposure.readings`) is withheld; since Codex review F1 also a receipt whose shown or revealed item is withheld now, or that names passages without their readings; since the re-review also one whose exposed revision is withheld by its frozen identity (`exposure.identities`, `Protection.covers_identity`), or that names an exposed item without one; an unreadable record is withheld; `_opportunity_withheld` resolves a lesson receipt by `lesson_id` |
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
  passages and no `readings` (closed before TE3a) cannot be judged and is withheld. At the Codex re-review (F1) the
  receipt also gains `exposure.identities` (each exposed item's revision as of the close, `source_identity`'s shape),
  revalidated by `Protection.covers_identity`; an exposed item without one is withheld. The re-review's residual
  (the identity was the revision current at the close) was reopened by the final verify and fixed at the landing
  (ruling R1): each identity is frozen when the lesson shows or reveals the item, on that turn's (or figure's)
  record, and `exposure.identities` is the union of every exposed revision's identity with the close's own.
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

## Landing onto main

Main was `23182034c6`: TE2 had landed as mvp-0.51 with migration 248 (`248_teacher_te2_sources.sql`), on the router
follow-up batch's mvp-0.50. The merge renumbered TE3a to **mvp-0.52 <- mvp-0.51** and its migration to **249**. While
the gate ran, main moved to `64f7d1dc86` (the teacher exam-question guard: no successor, no migration); it was merged
after the gate (below). The router speed stage had not landed.

### Orchestrator rulings (verbatim)

- R1: "F1 is fixed at the moment of exposure: each item's identity (practice_item_id, keys, whole, in AD's outside.source_identity shape, ids only) is frozen when the lesson shows or reveals it, on the turn's reveal or show record, and the closing receipt's exposure.identities is the union of every exposed revision's identity, never only the close-time one. AD's MaterialView keeps checking each identity with Protection.covers_identity and fails closed on a missing or malformed identity. Codex's reproduction (reveal pi_l1 citing ext_old/b1, replace pi_l1 with a public revision before close, close, protect ext_old/b1) is a test and must withhold the lesson. Build it so TE2's changes to teacher/service.py merge cleanly: keep the change to the reveal/show write and the receipt's exposure block. No further Codex round on this class; I read the diff before landing."
- R2: "The lesson prior's spread (first-dose sd 0.05, so the objective's lesson Q-bar equals RO4's placeholder draw for draw) rather than AD's new-kind width 0.070 is accepted, recorded as a labelled prior choice; once lessons give data the posterior moves it."
- R3: "Receipts closed before TE3a are withheld (fail closed): accepted, the census had no lessons. The receipt naming the readings a lesson read from (exposure.readings) and lesson minutes in AD's report row go to the follow-up batch, as recorded."
- R4: "Owner, Nov 5: the old item difficulty scalar is to be retired in the refactor. TE3a adds no new reader or writer of it; the landing checks this with a grep of the diff against main for the difficulty columns, mastery.irt.difficulty_from_prior and surprise's b, and records the result."

### Commits

| Step | Commit | What |
|---|---|---|
| R1 | `f60da20c5b` | Each display's frozen identities on its own record; the receipt's union; Codex's reproduction as a test (`docs/reviews/ad-te3a-codex-review.md`, "Final verify and landing ruling R1") |
| Merge, renumber | `6cad8141ec` | Main (`23182034c6`) merged. `LESSON_OPPORTUNITY_ALGORITHM_VERSION = mvp-0.52` after `TEACHER_PROBES_ALGORITHM_VERSION`; the upgrade's `PREDECESSOR` and completion are TE2's; the openers install TE3a's completion; `--to` names it; pyproject's source modules list it. Migration renamed 249; `migration_head_249` rebuilt from main's tracked `migration_head_248` with only 249 applied. Every defaults snapshot recomputed (all 43 moved: TE3a's key is in each, inert below its tag). value.py, readiness, objective_inputs and service.py resolved (below). R1 extended to TE2's probe card. CLI help snapshot regenerated |
| Pins | `dab159b1d1` | 14 pins the first mechanical pass missed (found by step 2): six head `MAX(version)` checks, five version sets ending at `LATEST`, the default upgrade's output, two by hand (`test_ad23_migration`, `test_help_assist_figures_migration`); the reference scripts' `SCHEMA_HEAD` |
| References | `49341f807e` | DB and configuration reference (head 249, 1181 effective leaves, the two prose counts 1180 -> 1181), desktop and module catalogs, vault validated |
| Merge | `7d9172c742` | Main (`64f7d1dc86`, the exam-question guard) merged without a source conflict; module references regenerated |

**The resolutions.**
- **value.py.** The follow-up batch's AD link (R9) and latent moments (R10) are kept, with TE3a's `LESSON` branch. With
  `ad_predictive_link` on, the rollouts' eta is AD's latent ability, the scale AD fits the lesson curve on, so the
  curve's shift adds there. Off, it adds on `logit p-bar`, as built. The curve is read from the same
  `decision_state_fields` call that, with the link, also carries `eta_moments`. The linked probe observation
  (`_observe` with the link, new on main) returned before it closed the lesson window; it now closes it too, as the
  unlinked branch does. The lesson Q-bar at the seeded prior equals RO4's placeholder, draw for draw, with every
  follow-up switch off and with them on (link with latent moments, monotone combiner, merged sessions, consistent
  review draw): `test_at_the_seeded_prior_the_lesson_q_bar_equals_ro4s_placeholder[off|on]`.
- **teacher/service.py.** TE2's `te2` payload and its receipt fields (`gaps`, `created_los`, `probes`) are kept with
  TE3a's `exposure.readings` and R1's `exposure.identities`.
- **R1 and TE2's probe card.** A served probe shows its question, so `probes.serve` writes the question's frozen
  identity on its `probe_served` record, and the receipt's union counts that record as a displayed one. Without
  this, every probe lesson's receipt would have failed closed. The identity helper moved to
  `learnloop.teacher.exposure`, which `service` and `probes` share.
  `test_landing_r1_a_probe_lesson_freezes_every_display_and_its_receipt_is_judged_not_failed_closed` drives TE2's
  probe end to end: every displayed record is frozen, the receipt has `identities` with the probe's, and AD's guard
  admits it until the probe's item is protected, then withholds it. The union test covers a served probe with
  identities and one without them (fails closed).
- **The head and the earlier migrations' pins.** TE2's 248 touches no table TE3a's 249 rebuilds.
  `test_ad23_migration`'s vault without 214 now reaches 248 (TE2's), and the runner applies `[214, 249]`. The
  altered-tables pins carry `TE3A_ALTERED_TABLES` again where main's side had been taken.

**R4.** `git diff 23182034c6 HEAD -- src migrations` (at `49341f807e`) adds no reader or writer of the difficulty
columns, `mastery.irt.difficulty_from_prior` or surprise's `b`. Its 32 added lines naming "difficulty" all name the
`adaptive_difficulty` package (imports, docstrings, the switch, the trace's source label). No added line names
`surprise`, `irt` or `difficulty_from_prior`.

### Gate

The gate ran at `49341f807e`. Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope
--quiet -p MemoryMax=5G -p MemorySwapMax=1G`. The full suite ran in 10G/2G under `flock /tmp/learnloop-fullsuite.lock`.
Every other Python or CLI ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No model call
or paid call was made.

| Command | Result |
|---|---|
| Step 2: targeted pytest, 262 files, `-n 6` (every file the merge touched, `test_te3a_*`, `test_teacher_*`, `test_ro*` (the `test_rofu_*` among them), `test_ad*`, `test_measurement_state_labels`, `test_codex_lockdown_round3`, the CLI help snapshot, the contract set) | 12254 passed, 20 skipped, 39 xfailed, 14 failed: all pins (`dab159b1d1`); their 14 files then 138 passed, 6 skipped, 1 xfailed |
| Step 3: `db_generate_reference` + `db_validate_reference` | errors [] (head 249; 1181 effective leaves, after the two prose counts) |
| Step 3: `desktop_generate` / `desktop_validate` | passed (321 TS/TSX + 6 Rust) |
| Step 3: `module_generate` / `module_validate` | PASS (1247 modules) |
| Step 3: `validate_vault.py` | passed (2238 notes) |
| Step 3: config fingerprints | all 43 snapshots recomputed; TE3a's successor test freezes main's mvp-0.51 value (`94291ed4...`, reproduced by dropping TE3a's key); every earlier frozen digest drops it (`drop_te3a_keys`) |
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| Full pytest (`-n 8 --dist worksteal`) | **29806 passed, 91 skipped, 47 xfailed, 2 failed** (59:03). Each failure passed alone 3 times: `test_rofu_carried::test_an_early_publication_served_keeps_its_carried_valuation` (the known flake TE2's record names) and `test_mvp021_upgrade::test_the_successor_rebuild_equals_mvp020s_projection` (a projection comparison, under the full suite's load) |
| Durability lane (`-m durability`) | 404 passed, 1 skipped |
| Owner lane on fresh backup-API copies of `owner-copies-mvp035` | 83 passed, 4 skipped, and the 2 known failures (`test_activity_backfill`, `test_placement_fixture_copies[arxiv_v2]`) |
| Desktop: typecheck, whole vitest (`--maxWorkers=4`), `frontend:build`, `cargo check` | ok, 2772 passed, ok, ok |
| Mobile: typecheck, build | ok, ok |
| After merging `64f7d1dc86` (teacher-guard-only): `test_teacher_*` (with `test_teacher_exam_question_guard`), `test_te3a_*`, `test_architecture`, `lint-imports` | 399 passed; 43 kept, 0 broken |

The full suite was not rerun after the guard's merge: it touched only the teacher's guards and their call sites
(no successor, no migration), so the teacher, TE3a and exam-guard files were rerun instead.

### Smoke

**Setup.**
- **Copies.** Fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy` (arxiv_v2, linear_algebra,
  probability), neutralized (every AI route at 127.0.0.1:9), under `fixtures-local/landing-te3a-smoke/` (since
  deleted).
- **Code.** `git archive` of main (`23182034c6`) and of the branch (`6cad8141ec`; the later commits change tests,
  references and records only), each with `migrations/`, run with that tree first on the path.
- **Upgrades.** On main code: mvp-0.45, rebuild, mvp-0.46, mvp-0.47, rebuild, then the default (mvp-0.51; head 248).
  On branch code: that copy opened once (migration 249 applied on open; mvp-0.51, head 249), then the default
  upgrade (mvp-0.51 -> mvp-0.52).

**Below the tag, and at the tag with `lesson_opportunities = false`.**
- **AD** (the replay's state hash, events fingerprint, opportunities and bank; `lo_readiness` for every LO;
  `decision_state_fields` with the learning moments; `report.build`): main at mvp-0.51 against the branch below the
  tag and against the branch at mvp-0.52 switched off. Identical on all three copies, the version label aside.
- **Today, Next and the follow-up gate** (the follow-up batch's driver: one day, seed pinned, the second item missed
  with FG1's follow-up written by `AuthorFake`, the first stop declined):
  - Below the tag: identical on each copy (Today, plan, every step, every router LLM and Decider request, the gate,
    every written row).
  - At the tag, switched off: as in RO5's, RO6's, the follow-up batch's and TE2's landings, the boundary key's
    version string seeds the rollouts' noise. It was set aside on both sides (`SMOKE_PIN_KEY`). So was the trace's
    generator key, which names the version. Without the key aside, the sessions diverged on linear_algebra (7
    attempts against 9). With both aside, everything was identical on all three copies: steps, Today, plan, the 5-6
    LLM and Decider requests, the gate and every row.

**At the tag** (switch on), through the real lesson handlers with the tests' `TeacherFake`:
- **Two lessons per copy, both closed `goal_reached`.**
  - Lesson 1 (R1): a teaching turn partly reveals item X, whose revision cites book blocks
    (`pi_a_causally_masked_transf`, `pi_linear_combinations_basis_recognize_01`,
    `pi_binary_mask_complement_story_proof`). X is rewritten with a public revision (no source refs) before the
    close. Then a check is answered right, the node lands and the lesson closes.
  - Lesson 2: a check answered right, then landed and closed.
- **Receipts.** Lesson 1's `exposure.identities` holds X's frozen pre-replacement identity; lesson 2's holds only
  the public one. Every displayed record carries its frozen identities.
- **AD's rows.** The sweep wrote one `lesson` row per lesson (`landed`, `salience_only`), and the replay reads both.
- **The report's lesson row.** `landed`: posterior, 2 lessons, first dose median 0.096 logit (90% 0.014 to 0.176),
  beside RO4's placeholder of 0.1. `taught`: 0 lessons. The `lessons_worse_than_no_lessons` flag is listed.
- **The lesson Q-bar at the prior.** The curve read at the decision is exactly the seeded prior (a lesson applied, no
  later cold answer). The lesson's Q with the curve equals RO4's placeholder draw for draw, with the follow-up switches
  off and on, on each copy (max draw difference 0.0).
- **AD's guard.** Raw reads of `lesson_receipts`, `lesson_turns` and `lesson_checks` inside an AD operation were
  refused, and each poisoned the operation.
- **Replay equivalence.** The live replay, a fresh run of the loaded events, the stored subject state after AD's
  rebuild, and the replay after a state sync were equal on each copy.
- **R1 on real data.** One block of X's old revision was protected (the held-out predicate patched in that process).
  X's current id stayed visible, and its frozen identity was covered.
  - On arxiv_v2 the block chosen is cited by nothing else either lesson exposed. The sweep at the new epoch
    withheld lesson 1 and kept lesson 2.
  - On linear_algebra and probability every block X cites is also cited by another revision lesson 2 exposed (a
    sibling item, or its book). Both lessons were withheld there, rightly.
- **`rebuild --shadow`** on each lesson copy: facet 0, schedule 0. Mastery changed by the `algorithm_version` stamp
  alone (mvp-0.47; arxiv_v2 33 rows, probability 17), except one row on linear_algebra: the lesson LO's
  `learning_object_mastery` (logit mean 1.152 live against 0.927 rebuilt). The same two lessons driven on **main's
  code** at mvp-0.51 give the same row with the same numbers, with or without X's replacement. So it is main's
  behaviour for a lesson check's mastery on that copy, not TE3a's. Recorded as an open item.
- **Calls and processes.**
  - No new `model_call_receipts`: 0 -> 0 on arxiv_v2 and linear_algebra, 56 -> 56 on probability (the backup's own
    Oct 25-26 receipts).
  - The socket watch logged no connect at all, no non-loopback address and no resolve.
  - The only subprocesses were `powerprofilesctl get` and `git -C` (the code stamp). No Codex process ran.

### What the owner runs after the fast-forward

For each vault (`~/learnloop-vaults/<name>`), once TE2's steps from its record are done (mvp-0.51):

```
learnloop upgrade --vault ~/learnloop-vaults/<name>        # mvp-0.51 -> mvp-0.52 (the default); migration 249 applies on open
learnloop rebuild-derived-state --vault ~/learnloop-vaults/<name>
```

Then rebuild the desktop app and restart the phone host, as for every landing. A vault still at an older tag reaches
mvp-0.52 through the chain with the same command.

To turn lesson opportunities off in a vault, add to its `learnloop.toml`:

```
[adaptive_difficulty]
lesson_opportunities = false
```

AD and the objective are then mvp-0.51's exactly. The lesson rows already recorded stay, unread.

### Open items

- **A lesson check's live mastery against its rebuild** (linear_algebra copy; on main too, above): for the follow-up
  batch.
- **R3's two items go to the follow-up batch**, as recorded: the receipt naming the readings a lesson read from, and
  lesson minutes in AD's report row.
- **Receipts closed before TE3a, and lessons open across the upgrade**, are withheld from AD (fail closed). A lesson
  open across the upgrade has displayed records without frozen identities; its receipt carries no `identities`.
