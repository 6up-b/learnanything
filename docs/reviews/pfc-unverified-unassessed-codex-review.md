# PF-c unassessed: Codex review fixes

Branch `fix/pfc-unverified-unassessed`, worktree `learnanything-pfc-unassessed`.
The review covered the stage at `f3659d02` (code commit `db81b807`). Codex
job: `~/.cache/codex-agent/jobs/20261012-133346-YMhiil`. Codex traced the
source but could not run anything (its sandbox could not create the `uv`
cache lock), so every finding was reproduced here first, as a failing test
where it was testable. All six findings reproduced. All six are fixed, one
commit each. No finding was rejected.

## Findings

| id | severity | title | verdict | commit | test |
|---|---|---|---|---|---|
| F1 | High | Unverified facets still get learner-field outcomes without an explicit map | fixed | `068fd00e` | `test_an_ordinary_item_gives_the_unverified_criterion_s_facet_nothing`, `test_a_criterion_without_targets_shares_its_facets_with_the_assessed_one`, `test_field_projection_and_timeline_read_unverified_criteria_the_same_way[targets_only]` |
| F2 | High | An entirely unassessed attempt can confirm a repair | fixed | `f9c42bf9` | `test_a_cold_retry_with_nothing_assessed_neither_confirms_nor_fails_the_repair[nothing_assessed]` (control `[assessed]`), `test_the_cold_verification_guard_refuses_an_unassessed_attempt_directly` |
| F3 | High | Pinned probes turn unverified points into authoritative observations | fixed | `d9710cb4` | `test_a_pinned_probe_declines_to_classify_an_unassessed_criterion[unverified_zero / unverified_partial]` (control `[assessed_zero]`) |
| F4 | High | Diagnosis history accepts unassessed criteria as recurring failures | fixed | `2606e810` | `test_a_later_diagnosis_cannot_cite_an_unassessed_shortfall_as_a_recurrence` |
| F5 | Medium | Reusing `mvp-0.10` mixes historical scores with changed evidence semantics | fixed (per-record boundary) | `04ada248` | `test_a_record_written_before_the_rule_keeps_its_interpretation_until_regraded`, `test_the_stamped_block_is_read_from_text_or_mapping`; real-base proof below |
| F6 | Medium | The informational review flag still excludes retention outcomes | fixed | `c43e8434`, `536543d2` | `test_retention_reads_the_pfc_flag_as_informational`, `test_retention_exclusions_distinguish_the_review_reasons` |

The docs commit `23ae5a0f` updates spec §5.5, Slice 1 M2 open question 3, and
the stage review. The stage review's Version section and its open questions 3
and 4 now point here.

The new tests are in `tests/test_pfc_unassessed_readers.py` (12 tests). In
`tests/test_pfc_unverified_unassessed.py`, the parity test now runs on the
ordinary item as well as the authored-map one, and the block test covers both
interpretations. Fakes only.

**Reproduction on the pre-fix code.** I ran both modules against `f3659d02`'s
`src` and `migrations`, with `PYTHONPATH` pointing at a `git archive` copy and
`-o pythonpath=`. 12 tests failed and 11 passed. The 11 that passed are the
two controls (F2 `[assessed]`, F3 `[assessed_zero]`) and the stage's other
nine tests. Each finding's test fails on the consequence the finding
describes:

| finding | failure on the pre-fix code |
|---|---|
| F1 | `covered_facets` = `{compute, recall}`, expected `{compute}`. The field's row is `{compute: 1.0, recall: 1.0}`. |
| F2 | A `causal_cold_verifications` row exists (`success = True`); the direct call does not raise. |
| F3 | One admitted `matched_single` observation is recorded (`matched_single_over_measured_features`). |
| F4 | `failed_criteria == ('result',)` on the cited attempt. |
| F5 | After a rebuild, the pre-rule record's debug payload has `unassessed_criteria` (it was reinterpreted). |
| F6 | `{'unresolved_grade': 3, 'intervening_practice': 1}`, expected `{'outcome_unassessed': 2, 'intervening_practice': 1}`. |

## What changed, per finding

### F1: the criterion→facet map comes from the rubric's targets

The issue was reproduced on the ordinary split-vault item. It has
`setup → compute` and `result → recall` as targets, no
`criterion_facet_weights`, and no lexical match.
`criterion_facet_weights_for_item` returns `{}`, so
`scale_coverage_for_graded_criteria` was a no-op. `derive_facet_outcomes` then
gave `recall` the attempt's outcome (1.0), in both the attempt step and the
learner field.

`learner/recall_coverage.target_criterion_facet_weights` reads the
projection's own map. It uses `compile_criterion_targets`, which takes authored
targets first. Without targets it takes the authored map's facets, and without
those the item's facets. Each target is weighted by its role, as
`allocate_success_mass` does. A criterion without targets keeps its authored
weights.

Both `scale_coverage_for_graded_criteria` and `derive_facet_outcomes` take an
optional `criterion_facet_weights` override. The attempt step
(`_compute_resolved_grade_application`) and the field (`field/outcomes._load`)
pass it only when a criterion is unassessed. A facet that only unassessed
criteria measure leaves coverage and has no outcome. A facet that assessed and
unassessed criteria share keeps the assessed share: on legacy criteria without
targets, both facets are scaled to 0.5 and get the assessed criterion's
outcome. Grades with nothing unassessed take exactly the old path.

### F2: no repair verification from an attempt with nothing assessed

The guard is in `record_delayed_cold_verification` itself, so no caller can
bypass it. It runs after the structural preconditions. If every current
evidence row of the cold attempt is unassessed, it raises
`ColdVerificationPrecondition("missing_chain", detail.reason =
"cold_attempt_unassessed")`.

The post-attempt hook records that as a typed §4.3 disposition and as the final
coldness receipt. Nothing else is written: no verification, no success, no
failure. `apply_cold_verification_to_factors` never runs, so the factor stays
`open` and its hypotheses stay `candidate`.

The test drives the full cold-retry path on an `mvp-0.10` vault: seeded factor
→ common repair → treatment → primed attempt → cold task → the cold attempt
through `apply_attempt` → `evaluate_attempt_intervention_followup`. It checks
the verification row, the disposition, the factor and both hypotheses. The
`[assessed]` control confirms the same path still resolves the factor as
`repair_confirmed`.

`missing_chain` was chosen because `causal_cold_outcomes.outcome` has a CHECK
vocabulary (migration 145) with no unassessed value. That table already uses
`missing_chain` for "the chain is incomplete, and that fact is the record". A
dedicated value would need a table rebuild (open question 1).

### F3: unassessed criteria supply no probe feature

`deterministic_probe_features` skips a criterion whose row is unassessed,
whatever points the grader left on it. A bundle that declares
`criterion:<id>:…` then fails the existing declared-feature completeness check
in `auto_classify_pinned_probe`, which declines and records nothing.

The tests cover zero-point and partial-point (2/4) unverified rows. The
partial row would read `passed = True` on the pre-fix code. An assessed-zero
control still classifies and resolves the factor.

### F4: the diagnoser's history

`history_attempt_from_blind_record` drops the record's
`grading_support.unverified_criterion_ids` from both `failed_criteria` and
`passed_criteria`. The stored-grade reader (`VaultHistoryStore._from_stored`,
used when no blind overlay is at hand) skips PF-c rows. It does not mistake an
attempt whose rows were all unassessed for one with no criterion rows (the
score-only fallback).

Both interpretations agree that an unverified criterion is no failure. The M2
reading already blocked its negative evidence, so this applies to pre-rule
records too. The test builds a later diagnosis through the real
`assemble_diagnosis_context` and `validate_diagnosis_proposal`, citing the
earlier attempt on `recall`. The citation is kept but marked
`cited_attempt_passed`, and nothing is validated. This does not touch the
grouping that Slice 2 T1 replaces; it only changes what counts as a failure.

### F5: a per-record interpretation boundary, not a reused tag

Codex was right that `mvp-0.10` history from before the rule exists. The Slice
1 M2 review documents upgrades to `mvp-0.10` and live blind-graded attempts on
`fixtures-local` copies, and main has carried the successor since then.
Calling the stage "amended before any vault ran it" was wrong.

There were two ways to fix it: a new algorithm successor, or a versioned
interpretation boundary. I chose the boundary, per record:

- **Each record names its interpretation.** A new unverified row's block is
  `{"negative_evidence_blocked": "valid_alternative_unverified",
  "unverified_interpretation": "unassessed", "targets": []}`. The blind
  record's `grading_support` carries the same key whenever the gate applied.
  A record without the mark was written before the rule.
- **Replay reads each record as written.** `unassessed_evidence_row` is true
  only for marked rows. `unverified_evidence_row` is true for either. A
  pre-rule row keeps its M2 reading: its kept points are credited, and its
  shortfall is blocked from negative evidence and from the unresolved-cause
  gate. The M2 `unverified_failure` branch is back in the projection for
  those rows only. Replay hands the shared step an empty unassessed set, and
  the persisted grade (the grader's own sum) stays paired with that evidence.
  A marked row is unassessed everywhere, as the stage built it.
- **The upgrade path is a regrade.** A regrade (the feedback screen's Regrade,
  sidecar `trigger_regrade`) grades the attempt again under the rule. It
  writes marked rows and the assessed grade, and replays.

Why per record and not a successor tag:

- Grader mode already works this way: it is per attempt, from the ledger,
  never read from config.
- A tag-level successor would still pair a pre-rule attempt's persisted
  grader-sum grade with the new evidence semantics on its next rebuild. That
  pairing is the mix Codex flagged, unless an upgrade also re-scored history.
  Re-scoring history is the reinterpretation that playbook rule 2 forbids
  without a correction event.
- A new tag would also take the label Slice 2 T1 expects to use.

No table, migration, default or upgrade function changed. Rules 2–8 of the
playbook are untouched.

**Proof on a record written by the real base implementation.** This is not a
simulation. I archived `22023ab4` (`src` and `migrations`) into the
scratchpad and used it to write a split vault under
`fixtures-local/pfc-f5-proof/`. The vault holds a PF-c partial answer (the
grader gave `result` 1/2), a nothing-assessed answer, and a wrong answer.

The base wrote:

- the unmarked block;
- a grade of 3/4 (0.75) and 0/4 (0.0) for the two PF-c answers;
- no `assessed_shortfall` in their grading support.

I made backup-API copies and rebuilt them under a frozen clock: twice with the
base code, once with the pre-fix stage (`f3659d02`), and once with this
branch. Every table was dumped. Columns that differ between the two base runs
were masked, and every ULID-shaped token was scrubbed.

| rebuild compared with base | tables | rows | result |
|---|---|---|---|
| this branch | 277 | 593 | identical |
| pre-fix stage (`f3659d02`) | 277 | 593 | 7 tables differ: `facet_capability_evidence`, `facet_recall_state`, `learning_object_mastery`, `practice_item_state`, `attempt_surprise`, `ability_transition_events`, `raw_grade_events` (the pre-rule records were reinterpreted) |

The only column that varies between the two base runs is
`attempt_debug_payloads.payload_json`. I compared it key by key: this branch
matches base on every key. The exception is the diagnosis receipt's
hypothesis-keyed entries, which also differ between the two base runs.

The unit test `_as_the_base_implementation_wrote_it` reproduces those three
write-time differences on the live door. The test checks the predecessor
replay, a new marked record next to it, and the regrade upgrade.

### F6: retention reads the PF-c flag as informational

`outcome_contract.retention_exclusions` reads two new row fields:

- `outcome_manual_review_reason`;
- `outcome_pfc_assessment` (`partially_assessed` / `nothing_assessed`), which
  `canonical_projection.pfc_assessments` computes from the outcome attempt's
  current marked rows.

The outcomes:

| outcome attempt | exclusion |
|---|---|
| PF-c reason, some criteria assessed | none (an ordinary label) |
| nothing assessed | `outcome_unassessed`, never `unresolved_grade` |
| any other review reason, or a pre-rule PF-c record | `unresolved_grade`, as before |

All three callers pass these fields:

- the scheduling evaluation's retention section, where
  `retention_label_rows` gains `outcome_manual_review_reason`;
- the dataset export's `R_next`;
- the data-quality report.

`outcome_contract` stays dependency-free. `PFC_REVIEW_REASON` is pinned equal
to `UNVERIFIED_REVIEW_REASON` by a test.

`LABEL_VERSION` is unchanged. Eligibility is unchanged for every label written
before this branch, and for every joint label: joint vaults never carry the
reason (see the rebuild proof below). Only new marked PF-c outcomes are read
differently (open question 3).

## Claims that did not hold

| Codex's point | Now |
|---|---|
| "Unassessed everywhere" / field and projection agree | They agree on items without an authored map too (F1). The parity test runs both ways. |
| "Nothing assessed … the attempt is no evidence" | Also true for repair verification (F2) and probe classification (F3). |
| The review reason is only a non-blocking log | Retention now reads it as one (F6). |
| "Amended before any vault ran it" | Withdrawn. The `algorithm_versions.py` note, spec §5.5 and M2 open question 3 now describe the per-record boundary (F5). |

## Joint vaults rebuild identically (re-checked on the fixed branch)

I made backup-API copies of the worktree's committed fixtures under
`fixtures-local/pfc-review-proof/`. The owner's live databases were not
touched, and the tracked fixtures are unchanged (`git status` clean). Each
copy was rebuilt twice with base `22023ab4` and once with this branch, under a
frozen clock. All tables were compared with the columns that vary between the
two base runs masked. (These rebuilds, and the F5 proof, ran on the fixed
code before two later edits that no rebuild reaches: the history loader's
substring pre-check and `536543d2`'s import move.)

| fixture copy | tables | rows | masked columns (vary between base runs) | base vs branch |
|---|---|---|---|---|
| `migration_head_170` | 277 | 655 | `activity_administrations.administration_snapshot_hash`, 3 `grade_interpretations` columns, `grader_calibration_models.content_hash`, `measurement_events.payload_json` | identical |
| `linear_algebra` | 277 | 13,633 | `administration_snapshot_hash`, `attempt_debug_payloads.payload_json`, `schema_migrations.applied_at` | identical |
| `probability` | 277 | 6,032 | `administration_snapshot_hash`, `schema_migrations.applied_at` | identical |
| `arxiv_v2` | 277 | 9,067 | `administration_snapshot_hash`, 3 `grade_interpretations` columns, `measurement_events.payload_json`, `schema_migrations.applied_at` | identical |

## Paid calls

None. Every test uses fakes, and no external interface needed checking.

## Gate

Run on `536543d2` (the last code commit before this file).

The first full-suite run, on `23ae5a0f`, gave **1 failed, 7291 passed**. The
failure was `test_architecture::test_function_local_domain_imports_match_the_frozen_edge_inventory`:
F6's function-local import added a new cross-domain edge,
`scheduling.evaluation -> substrate.canonical_projection`. `536543d2` moves
that import to module level, as other scheduling modules import `substrate`;
no import cycle results. Both lanes were then rerun:

- `uv sync --extra dev` and `uv pip install pypdfium2`: done. `learnloop_mobile`
  is untouched, so no `--extra mobile`.
- `uv run lint-imports --no-cache`: **10 kept, 0 broken**.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`: **7292 passed**,
  0 failed, 14 warnings, 155 s.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`:
  **77 passed**, 7215 deselected, 79 s.
- Frontend: not changed in this step (`git diff f3659d02 HEAD -- apps/` is
  empty). Run anyway: `npm run typecheck` clean; `npm test` **74 passed in
  18 files** (no `npm install` needed; dependencies unchanged).
- Schema: unchanged (no migration; one `SELECT` gains a column alias), so the
  DB reference scripts were not needed.
- `git diff --check`: clean. Tracked fixtures: unchanged.

## Open questions

1. **Disposition vocabulary.** An unassessed cold retry is recorded as
   `missing_chain` (`detail.reason = cold_attempt_unassessed`), because
   `causal_cold_outcomes`'s CHECK has no unassessed value. Add a dedicated
   value? It would need a migration that rebuilds the table.
2. **Upgrade path without a model call.** Pre-rule PF-c records move to the
   rule only through a regrade, which is a fresh grading call. If the owner
   wants it, a model-free reinterpretation is possible: a correction event
   that re-stamps the rows and re-scores the attempt from the same points.
   Few such records should exist: only `mvp-0.10` blind grades where the gate
   fired, on M2-era copies.
3. **`LABEL_VERSION` / `OUTCOME_VIEW_VERSION`.** Neither was bumped. Retention
   eligibility changes only for marked PF-c outcomes. The field's view changes
   only for PF-c attempts on items without an authored map. That covers
   pre-rule ones too, because the field has treated every unverified criterion
   as unassessed since M2, and F1 corrects how it applied that. Bump either
   label anyway?
4. **The current attempt's context.** A diagnosis now runs only for an
   assessed shortfall. The current attempt's context still passes its blind
   record through as written, including an unverified criterion's points.
   History no longer does. Strip it there as well?
5. **History score.** History shows the blind record's own `rubric_score`,
   which is the grader's sum, not the applied grade. It is display only and no
   longer drives failures. Show the applied grade instead?

## Re-review

Codex re-reviewed the branch at `7a30f8e6`. Codex job:
`~/.cache/codex-agent/jobs/20261012-143407-BB44Hl`. It confirmed F1–F5 fixed,
reopened F6, and raised one new finding, F7. It ran no integration tests
(read-only sandbox), so its checks were database-free. F6 and F7 describe the
same defect. I reproduced it here first, as failing tests on `7a30f8e6`, then
fixed both in one commit.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Unverified facets still get learner-field outcomes without an explicit map | confirmed fixed | `068fd00e` | no change |
| F2 | High | An entirely unassessed attempt can confirm a repair | confirmed fixed | `f9c42bf9` | no change |
| F3 | High | Pinned probes turn unverified points into authoritative observations | confirmed fixed | `d9710cb4` | no change |
| F4 | High | Diagnosis history accepts unassessed criteria as recurring failures | confirmed fixed | `2606e810` | no change |
| F5 | Medium | Reusing `mvp-0.10` mixes historical scores with changed evidence semantics | confirmed fixed | `04ada248` | no change |
| F6 | Medium | (reopened) The exemption also admits grades with a separate unresolved concern | fixed | `eea629fc` | the F7 tests |
| F7 | Medium | PF-c retention exemption masks genuinely unresolved grades | fixed | `eea629fc` | `test_a_separate_review_concern_survives_the_pfc_flag[low_grader_confidence / grader_recommended]`, `test_nothing_assessed_is_read_from_the_evidence_not_the_review_reason`, `test_retention_exclusions_keep_the_pfc_state_and_the_review_independent`; control `test_the_pfc_flag_is_the_reason_only_when_it_is_the_sole_concern` |

### Reproduction on the pre-fix code

I ran `tests/test_pfc_unassessed_readers.py` against `7a30f8e6`'s `src`, using
a `git archive` copy on `PYTHONPATH` with `-o pythonpath=`. Result: 4 failed,
13 passed. The control and the 12 earlier tests passed.

| test | failure on `7a30f8e6` |
|---|---|
| `…survives_the_pfc_flag[low_grader_confidence]` | The outcome was graded at confidence 0.2 with `setup` assessed and `result` unverified. The scheduling evaluation excluded `{}`: the label was eligible. The attempt's reason was `valid_alternative_unverified`. |
| `…survives_the_pfc_flag[grader_recommended]` | Same failure, for a grade where the grader itself set `manual_review_recommended`. |
| `…read_from_the_evidence_not_the_review_reason` | The outcome had nothing assessed and its review cleared. Excluded `{'intervening_practice': 1}`, expected `{'intervening_practice': 1, 'outcome_unassessed': 2}`. |
| `…keep_the_pfc_state_and_the_review_independent` | Nothing assessed plus another reason gave `['outcome_unassessed']`, expected `['outcome_unassessed', 'unresolved_grade']`. |

Codex's chain needs one correction; the consequence is the same. Validation
never reaches `low_grader_confidence`. The gate sets
`manual_review_recommended` on the proposal, so validation's first-match chain
stops at `codex_manual_review`. The attempt step then replaced that with the
PF-c reason. Two other concerns were masked the same way: the grader's own
review recommendation and a pending clarification
(`provisional_pending_clarification`). The masking itself dates from Slice 1
M2. F6's exemption is what let it reach retention.

### What changed (`eea629fc`)

- **The reason.** `grading_support.gated_review_reason` returns `None` when
  the gate did not apply. When it did, it validates the grader's proposal as
  the grader returned it, before the gate. That proposal is the modal one and
  is now kept on `BlindGradingRun.ungated_proposal`. If that validation gives
  any reason, the attempt keeps it. The PF-c reason is recorded only when the
  gate is the grade's sole review concern. The live door
  (`_complete_blind_graded_attempt`) and the regrade both use it. A PF-c
  attempt that carries another reason stays `manual_review` with that reason,
  so retention reads it as `unresolved_grade`. The PF-c state is still on the
  evidence rows and the blind record.
- **The contract.** `retention_exclusions` now checks the two conditions
  independently. Nothing assessed gives `outcome_unassessed`. A review gives
  `unresolved_grade` unless its reason is PF-c on a marked attempt. Both can
  apply to the same outcome.
- **The callers.** The scheduling evaluation, the dataset export and the
  data-quality report now read `pfc_assessments` for every outcome. Before,
  they read it only for attempts carrying the PF-c reason. A nothing-assessed
  outcome therefore stays excluded when its reason is another concern, and
  when the reason has been cleared. `expire_clarifications` is the one writer
  that clears it, and a PF-c grade can now reach it.
- **Docs.** Spec §5.5 (`spec_embedding_consumers_v1.md`) and the stage
  review's open question 4 now say the flag is the reason only as the sole
  concern.

Other effects:

- **Feedback screen.** A PF-c grade with a separate concern shows that concern
  ("manual review recommended: low_grader_confidence") instead of the
  different-route note. Its criterion rows still read "not assessed (a
  different route)". No frontend change was needed.
- **Clarifications.** A PF-c grade with a licensed clarification now reads as
  provisional, as every other grade with one does. The clarification row was
  already recorded either way.
- **Blind record.** It keeps the gated grade's own reason, as M2 wrote it.
  Nothing reads that field.
- **Cost.** A gated blind grade costs one extra deterministic validation. It
  makes no model call.

### Joint-vault retention readers are unchanged

I made backup-API copies of the worktree's committed fixtures under
`fixtures-local/pfc-f7-proof/`. I ran the three retention readers on each copy
with `7a30f8e6` and with this branch. The readers were the evaluation's
retention section, the dataset's `R_next` exclusions per source, and the
data-quality report. All outputs matched. The one masked field was the
report's `generated_at`, which also varies between two runs of the same code.

| copy | eligible labels | exclusions | `R_next` rows | pre-fix vs fixed |
|---|---|---|---|---|
| `migration_head_170` | 1 | hinted 1, insufficient_delay 1, same_session 1 | 6 | identical |
| `linear_algebra` | 1 | hinted 1, insufficient_delay 15, intervening_practice 10, same_session 2 | 70 | identical |
| `probability` | 0 | insufficient_delay 1, primed 1, same_session 1 | 2 | identical |
| `arxiv_v2` | 0 | none | 3 | identical |

No rebuild was needed. The change touches only the grading write path and
read-only readers, and replay does not regrade.

### Paid calls

None. Every test uses fakes, and no external interface needed checking.

### Gate (re-review)

Run on `eea629fc`.

- `uv sync --extra dev` and `uv pip install pypdfium2`: done. `learnloop_mobile`
  is untouched, so no `--extra mobile`.
- `uv run lint-imports --no-cache`: **10 kept, 0 broken**.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`: **7297 passed**,
  0 failed, 14 warnings, 228 s. That is the earlier 7292 plus the 5 new tests.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`:
  **77 passed**, 7220 deselected, 66 s.
- Frontend: unchanged (`git diff 7a30f8e6 HEAD -- apps/` is empty), so it was
  not run.
- Schema: unchanged (no migration), so the DB reference scripts were not
  needed.
- `git diff --check`: clean. Tracked fixtures: unchanged.

### Open question (new)

6. **The grader's own review recommendation next to PF-c.** It is now a
   blocking review: the outcome stays out of retention, and the feedback
   screen shows the review. A grader that sets `manual_review_recommended`
   whenever it declares a criterion unverified would keep most PF-c outcomes
   out of retention. Those outcomes were all out before F6, so this costs no
   labels compared with the original stage. I kept the recommendation
   blocking because it is the grader's explicit statement. The other choice
   is to treat a recommendation that only accompanies declared unverified
   criteria as part of the PF-c log. That would read the grader's intent,
   which I can't verify.
