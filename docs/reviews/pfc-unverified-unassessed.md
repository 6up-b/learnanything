# PF-c unverified criteria are unassessed everywhere (inside mvp-0.10)

> **Integration note (merge into main, 2026-10-12, merge branch `merge/pfc`
> from `e9ced35e`).** Main had gained mobile M1, Slice 2 T8 (v3), T4 and T5,
> Slice A Phase 6 placement (`mvp-0.11` = M2's split plus placement;
> migrations 172/173) and Phase 5a PF generation (174). Where this record and
> the Codex review say otherwise, this note is current.
>
> - **No textual conflicts.** Git merged every file cleanly. The semantic
>   compositions are below. One test path moved: the joint-fixture replay test
>   now copies `fixtures/migration_head_174` (main renamed the head fixture).
> - **Versions: at or after, by record.** The branch adds no version gate. PF-c
>   rows and blind records are written only by the blind grader, which runs at
>   every `DIAGNOSIS_SPLIT_VERSIONS` member (`split_grading_active`, set
>   membership: `mvp-0.10` and `mvp-0.11`). Replay reads each record's own
>   interpretation mark. So the rule applies at `mvp-0.11` exactly as at
>   `mvp-0.10`, and joint vaults (`mvp-0.9` and earlier) never reach it. The
>   `algorithm_versions.py` note and the projection comment now say "the split
>   versions" instead of "this version". The core tests (complement route,
>   nothing assessed, regrade, split replay/rebuild) are parametrized over
>   `DIAGNOSIS_SPLIT_VERSIONS`. The placement tests already grade at
>   `mvp-0.11`.
> - **Placement reads PF-c's own marker.** Phase 6's
>   `placement.state.pfc_unverified_attempt_ids` found PF-c attempts by
>   `manual_review_reason = valid_alternative_unverified` and inferred "no
>   assessed shortfall" from the points. Since this branch, the reason is a log
>   recorded only as the grade's sole concern (F7), and it can be cleared
>   (`expire_clarifications`). It now reads the stamp on the current evidence
>   rows. For rows marked `unverified_interpretation = unassessed`, it reads
>   the gate's `assessed_shortfall` from the attempt's latest blind grade
>   record. A row written before the rule (unmarked, no `assessed_shortfall`)
>   keeps M2's points inference. Placement's behaviour is unchanged: a PF-c
>   answer is unassessed, ineligible at the check, never a lapse, and skipped
>   by fast-track and the quick check. No new placement behaviour was added.
>   One edge case now follows the gate instead of the points. An error the
>   gate left in force (located in the learner's words) is an assessed
>   shortfall even when every assessed criterion has full marks. Placement now
>   reads it as a miss, where M2's points inference read it as unassessed. The
>   same flag now queues the diagnosis.
>   The owner's pending stage decides the 14-day check by the diagnosis.
>   `placement.rules` pins `PFC_UNASSESSED_INTERPRETATION_KEY` and its value to
>   the projection's constants by a test, because placement may not import
>   `substrate`.
>   `tests/test_placement_split_grades.py`:
>   - one assertion changed with the mechanism: an unverified PF-c answer's row
>     now reads `correctness == 1.0` (the grade over the assessed criteria), not
>     `< 1.0`;
>   - four tests were added. Two fail when the reason-based detection is
>     combined with this branch's grading: a PF-c grade whose reason names
>     another concern was a miss (`failed`, back to learning), and one whose
>     review was cleared passed the check (`maintenance`). Both now wait.
>     Two pin unchanged behaviour: an assessed shortfall beside an unverified
>     criterion is still a miss, and a record written before the rule still
>     waits.
> - **Phase 5a agrees.** The `valid_alternative` compare suite grades
>   CAS-verified synthetic traces with the blind grader's raw proposal
>   (`blind_grading_context` and `blind_grading_prompt`, no reference policy
>   and no gate). It measures raw false rejection, which is the population the
>   PF-c gate catches in production. This branch changes neither the prompt,
>   its version, the context nor the gate's trigger. It changes only what the
>   gate's verdict does downstream. So the suite's numbers keep their meaning
>   and stay the "before the gate" arm. `solver_panel` difficulty reaches the
>   attempt step through `item_irt_params`. A nothing-assessed attempt skips
>   the mastery and EB-difficulty steps, whatever the difficulty source. All
>   5a tests pass unchanged.
> - **Config and references.** No config default changed, so
>   `DEFAULTS_SNAPSHOT_BY_ALGORITHM` is untouched, and `DEFAULT_CONFIG_TEXT` is
>   unchanged. The CLI is unchanged. The schema is unchanged (head 174). The
>   DB/config references were regenerated only for the source-line citations
>   and commit stamps the edits moved. The prose counts are unchanged: 291
>   table notes, 615 effective config leaves in 36 section notes.
> - **Parity proof** on backup-API copies of this worktree's committed
>   `linear_algebra` and `probability` fixtures (`fixtures-local/pfc-merge-proof/`).
>   Each copy was rebuilt with `rebuild_all_derived_state` under a frozen
>   clock: twice with main's code (`git archive e9ced35e`) and once with the
>   merge. `mvp-0.9` and `mvp-0.11` were reached with main's own
>   `learnloop upgrade` before copying. Every table was dumped and ULID tokens
>   were scrubbed. Columns that still vary between the two main runs were
>   masked: `activity_administrations.administration_snapshot_hash`, and on
>   `linear_algebra` `attempt_debug_payloads.payload_json`. That column was
>   then compared key by key (18,318 paths over 70 payloads), masking only
>   `causal_attribution.diagnosis_receipt(s).id`, which also varies between
>   main runs.
>
>   | copy | version | tables | rows | main vs merge |
>   |---|---|---|---|---|
>   | `linear_algebra` | mvp-0.8 (as committed) | 291 | 13,638 | identical (debug payloads identical key by key) |
>   | `linear_algebra` | mvp-0.9 | 291 | 13,947 | identical (debug payloads identical key by key) |
>   | `probability` | mvp-0.8 (as committed) | 291 | 6,037 | identical |
>   | `probability` | mvp-0.9 | 291 | 6,346 | identical |
>   | `linear_algebra` | mvp-0.11 (joint history) | 291 | 13,951 | identical (debug payloads identical key by key) |
>   | `probability` | mvp-0.11 (joint history) | 291 | 6,350 | identical |
>
> - **Gate** (on the merge tree, before the commit). No paid calls; fakes only.
>   - `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: done.
>   - `uv run lint-imports --no-cache`: **12 kept, 0 broken**.
>   - `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto -q`:
>     **7894 passed**, 0 failed.
>   - `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability -q`:
>     **85 passed**, 7809 deselected.
>   - Frontend: `npm install` ok (up to date), `npm run typecheck` clean, and
>     `npm test` **103 passed in 23 files**.
>   - `db_validate_reference.py`: **0 errors** (schema 174). `validate_vault.py`
>     passed. The module and desktop reference validators fail on main as
>     well, with the same 290 issues and the same `TypeScript/screens/today`
>     KeyError. This merge adds no module and changes neither.
>   - Tracked fixtures unchanged.

Branch `fix/pfc-unverified-unassessed`, worktree `learnanything-pfc-unassessed`,
base `22023ab4`. Answers Slice 1 M2 open question 3 (owner decision,
2026-10-12): a route that never exercised a criterion's skill tells us nothing
about that skill, so an unverified criterion is neither credit nor failure,
consistently.

## What was there

The valid-alternative gate (`attempts/grading_support.py`,
`apply_valid_alternative_gate`) fires when the deterministic final-answer check
says the learner's concluding line equals the reference, but the blind grader
marked a criterion below full points without locating a concrete error in the
learner's words. Before this branch the gate:

- rescoped the grader's attributions on that criterion to
  `grader_interpretation`;
- stamped the criterion's grading-evidence row with the block
  `valid_alternative_unverified`, so the projection banked no negative mass;
- set `manual_review_reason = valid_alternative_unverified`;
- kept the grader's partial points. They counted in `rubric_score`, so in the
  FSRS rating, in the learning-object mastery update and as positive facet
  evidence in the canonical projection and the evidence timeline.

The Slice 1 M2 merge had already made the learner field read such a criterion
as unassessed (`field/outcomes.py`). The field and the projection disagreed.

## The rule (as built)

**Score.** `attempts.assessed_rubric_score` replaces the derived score whenever
the gate recorded unverified criteria:

- `fraction = Σ awarded / Σ max` over the **assessed** criteria (rubric
  criteria not unverified; awarded points clamped to each criterion's maximum,
  a missing row counts 0, as in the validator's derived score);
- `rubric_score = round(fraction × rubric.max_points)`, clamped to
  `0..max_points`, then the fatal-error caps apply as before;
- **nothing assessed** (every rubric criterion unverified): `fraction = 1`.
  The deterministic final-answer check has verified the answer, so it is correct
  for scheduling. Fatal caps still apply ("score rules otherwise unchanged").
- With nothing unverified it returns `calculate_rubric_score` exactly, so every
  other grade is bit-for-bit unchanged.

Why rescale onto `0..max_points` instead of storing a reduced denominator:
every reader of the grade reads `rubric_score` against `rubric.max_points`.
These readers are `correctness`, `fsrs_rating_for_attempt`, the grade channel's
observed class, the LO mastery observation, the feedback bundle, the field's
memory arm, the offline FSRS fit and review-log reconstruction. A per-attempt
denominator would need a new column and a second code path in each of them
(requirement 2 forbids a separate scheduling path). The rescale keeps one
integer grade whose fraction is the assessed fraction. It is the construction
teach-back already uses for its asked criteria (`asked_rubric_score`). Rounding
is the same `int(round(...))` the derived score uses. On the 2+2 rubrics the
assessed fraction is exact.

Example (the tests' item: `setup` 2 points, `result` 2 points). `result` is
unverified with 1 kept point, `setup` is 2/2. The grader's sum is 3/4 (`good`).
The grade is now 4/4 (`easy`). If `setup` were 1/2, it would be 2/4.

**Scheduling.** The FSRS rating is `fsrs_rating_for_attempt(item,
rubric_score, …)` on that grade. The grade is persisted on the attempt, and
replay reads the persisted grade, so there is no second path.

**Mastery and evidence.** One test, `canonical_projection.unassessed_evidence_row`,
reads the stamped block (text or decoded). An unverified criterion is treated
like a criterion nobody graded (projection v6):

- *Canonical projection*: no outcome at all. No positive mass (the kept points
  are no longer credited), no negative mass, no unresolved-cause factor, and it
  does not localize its descendants. The M2 `unverified_failure` branch is gone,
  because an unverified criterion never reaches it.
- *Evidence timeline* (`facet_evidence_timeline`): the same skip, so the
  Demonstrated curve still equals banked credit. Before this branch the timeline
  credited the kept points too, and it marked a surface group for the blocked
  failure that the projection skipped.
- *Attempt step* (`_compute_resolved_grade_application`): the criterion leaves
  the criterion vector. It certifies no facet mass and has no facet outcome,
  exactly like an ungraded teach-back criterion. It is also left out of the
  passed-target firewall and the facet-uncertainty rows, and its raw grade event
  classes it `unassessable`.
- *Nothing assessed*: zero facet mass (an empty vector would otherwise read as
  "no criterion information", which means legacy full mass). The learning
  object's mastery is left exactly as it was (no EKF step, no variance floor, no
  EB-difficulty update). Scheduling still reads the correct grade. This matches
  the field, which writes no outcome row for such an attempt, and the projection,
  which writes nothing.

Live grades, regrades and replay all go through these paths. The live and
regrade doors compute the score. Replay reads the persisted score, and reads
the unverified set back from the stamped rows (never from config).

**Diagnosis.** `needs_diagnosis` reads a new gate field, `assessed_shortfall`.
It is true for a below-full criterion that is not unverified, or for an
attribution the gate left in force. When the gate applied, only that or a fatal
error queues the live diagnosis. So no card explains a shortfall that was not
assessed. A blind record written before this field existed reads as before.

**Review flag.** `manual_review_recommended`, `manual_review` and
`manual_review_reason = valid_alternative_unverified` are still recorded,
unchanged, as a log. Nothing waits on them. The feedback screen's
"manual review recommended" toast is replaced, for this reason only, by an
informational line. The inspector's amber "manual review" pill becomes a slate
"different route" pill.

**Learner-facing feedback.**

- *Attempt result / feedback screen*: `criterion_evidence_dto` gains `assessed`
  and `not_assessed_label`. The criterion row shows a neutral mark, the pill
  "not assessed (a different route)" and no points. The "evidence this attempt"
  chip is neutral. The score line shows the assessed grade.
- *Diagnosis card*: it never shows points. With the trigger change, an attempt
  whose only shortfall is unverified gets no card (`not_needed`).
- *TUI*: the rubric evidence block prints `– result  not assessed (a different
  route)` instead of points.
- *Inspector*: the same treatment as the feedback screen.

## Version

> **Superseded by the Codex review (F5,
> `docs/reviews/pfc-unverified-unassessed-codex-review.md`).** The claim
> below that no history exists at `mvp-0.10` is wrong: the Slice 1 M2 live
> runs graded blind attempts at `mvp-0.10`. The boundary is now per record:
> every new unverified row and blind record names its interpretation
> (`unverified_interpretation = "unassessed"`), a record without the mark
> replays as the M2 implementation wrote it, and a regrade rewrites it under
> the rule. Open questions 3 and 4 below were fixed there too (F4, F6).

**This lives inside `mvp-0.10`.** No algorithm tag was added, and the
projection namespace is unchanged.

- The playbook (`docs/algorithm-change-playbook.md`) does not address amending
  a merged successor that no vault has run. Its rule 1 ("Never silently reuse an
  old tag") protects history written under a tag. No history exists at
  `mvp-0.10`: PF-c and the blind prompt run only in split vaults at `mvp-0.10`.
  The owner's vault configs are at `mvp-0.8`, the tracked fixtures are at
  `mvp-0.8` (`migration_head_170` is at `mvp-0.6`), and the upgrade is an
  owner-run command. The amendment is not silent: it is recorded in
  `algorithm_versions.py` (the `mvp-0.10` comment), in spec §5.5, in Slice 1 M2
  open question 3, and here. Rules 2–8 are untouched: no ledger is rewritten,
  no table is added, no default changes, no upgrade function changes.
- `CANONICAL_PROJECTION_VERSION` is **not** bumped. The fold changes only for
  rows that carry the PF-c block, which only `mvp-0.10` blind grades write. A
  bump would surface a recalibration boundary ("estimates recomputed") on every
  joint vault's next rebuild with nothing recomputed, and it would break the
  joint byte-identity this stage must keep.
- The `mvp-0.10` defaults fingerprint is **not** recomputed: no config default
  changed.

**Joint vaults rebuild byte-identically.** The proof was run on
`fixtures-local/pfc-proof/` backup-API copies of the tracked fixtures, taken
from this worktree's committed files (never the owner's live databases). Each
fixture was copied three times and rebuilt with `rebuild_all_derived_state`
under a frozen clock: twice with the base code (`git archive 22023ab4 src
migrations` on `PYTHONPATH`) and once with this branch. Every table was then
dumped. Two comparisons were made:

1. *Masked*: columns that differ between the two base runs are surrogate ids,
   their hashes and the calibration/debug JSON that embeds them. They are
   masked, and base is compared with the branch on everything else.
2. *Scrubbed*: every ULID-shaped token is replaced, then the dumps are compared
   again. The only columns still volatile base-vs-base are
   `activity_administrations.administration_snapshot_hash`,
   `schema_migrations.applied_at`, two id/hash columns of
   `grade_interpretations` and `grader_calibration_models`, the
   `measurement_events.payload_json` ids, and (`linear_algebra`) only the
   diagnosis-receipt ids inside `attempt_debug_payloads.payload_json`.
   Base-vs-branch differs in exactly those keys and nothing else.

| fixture copy | version | tables | rows | masked | scrubbed |
|---|---|---|---|---|---|
| `linear_algebra` | mvp-0.8 | 277 | 13,633 | identical | identical |
| `probability` | mvp-0.8 | 277 | 6,032 | identical | identical |
| `arxiv_v2` | mvp-0.8 | 277 | 9,067 | identical | identical |
| `migration_head_170` | mvp-0.6 | 277 | 655 | identical | identical |
| `linear_algebra`, rebuilt with the version forced to mvp-0.10 | mvp-0.10 | 277 | 13,633 | identical | identical |

The learner field's `data_check` was also run on the three owner-fixture copies
with base and branch code. Leaving out the `limitations` prose (one sentence was
reworded; see below), the outputs are identical.

## Files

- `src/learnloop/attempts/attempts.py`: `assessed_rubric_score`; the live door
  (`complete_codex_graded_attempt`) grades over the assessed criteria; replay
  reads the unverified set from the stamped rows; the shared step leaves
  unassessed criteria out of coverage, outcomes, the firewall and the
  facet-uncertainty rows, and with nothing assessed writes no facet mass and no
  LO mastery step; the grade-channel dual write classes them `unassessable`; the
  debug payload gets `unassessed_criteria` (only when non-empty).
- `src/learnloop/attempts/regrade.py`: the regrade's grade over the assessed
  criteria.
- `src/learnloop/attempts/grading_support.py`: `GateOutcome.assessed_shortfall`
  (persisted in `grading_support`), `UNASSESSED_CRITERION_LABEL`, docstrings.
  The grader prompt is unchanged (same prompt version and calibration identity).
- `src/learnloop/substrate/canonical_projection.py`: `unassessed_evidence_row`,
  and the projection skip.
- `src/learnloop/learner/facet_evidence_timeline.py`: the mirrored skip.
- `src/learnloop/diagnosis/split/live.py`: `needs_diagnosis` reads
  `assessed_shortfall`.
- `src/learnloop/field/outcomes.py`: comments and the limitation sentence only.
  Behaviour and data-check counts are unchanged. The debug-validation skip of
  PF-c attempts is kept, so `compared` / `mismatched` keep their meaning (the
  live debug outcome now agrees with the field there anyway).
- `src/learnloop_sidecar/handlers/serializers.py`: `assessed` and
  `not_assessed_label` on criterion rows.
- `src/learnloop/tui/screens/feedback.py`: the not-assessed row.
- `apps/learnloop-tauri`: the DTO fields, the feedback criterion row, the
  evidence chip, the informational PF-c line, and the inspector rows and pill.
- `src/learnloop/algorithm_versions.py`: the `mvp-0.10` note.
- `docs/specs/spec_embedding_consumers_v1.md` §5.5 and
  `docs/reviews/slice-1-m2.md` open question 3.

No migration, no schema change, no config default change.

## Tests (fakes only)

New: `tests/test_pfc_unverified_unassessed.py` (10 tests) and one vitest case
in `FeedbackScreen.test.tsx`.

The base check ran the new module against the base code (`22023ab4` on
`PYTHONPATH`, with `-o pythonpath=` pointing at it, and local stand-ins only for
the two new symbols the module imports). 9 of the 10 tests fail on the base
code:

| test | fails on base with |
|---|---|
| complement route graded on its assessed criteria | grade `(3, 0.75)`, expected `(4, 1.0)` |
| no assessed criterion: correct for scheduling, no evidence | grade `(0, 0.0)`, expected `(4, 1.0)` |
| located error beside an unverified criterion | no `assessed_shortfall` on the gate |
| regrade applies the same rule | regraded grade `(3, 0.75)` |
| split replay/rebuild keep them unassessed | live grade `(3, 0.75)` |
| joint grades replay untouched beside blind unverified ones | blind grade `(3, 0.75)` |
| joint fixture replays through the unchanged path | no unassessed set reaches the shared step |
| field, projection and timeline agree | the projection credits `recall` (0.565 vs 0.522) |
| feedback shows "not assessed" | no `assessed` key on criterion rows |

The tenth test (reading the block from text or a mapping) tests only the new
helper.

The vitest case fails on the base frontend ("Unable to find … not assessed (a
different route)") and passes here.

The joint-vault parity tests (`test_joint_grades_replay_untouched_beside_blind_unverified_ones`
and `test_joint_fixture_replays_through_the_unchanged_path`, the latter in the
durability lane) pin an invariant the base already satisfies for joint rows.
They fail on base only through the blind half or the new seam. The byte-for-byte
proof is the fixture rebuild above.

The criterion→facet map is authored in the tests' vault
(`criterion_facet_weights`), so the attempt step, the field and the projection
measure the same facets. With the inferred map, these items have no
criterion→facet mapping, and the attempt step and the field fall back to the
attempt's outcome for every facet.

## Paid calls

None. No real provider call was needed or made.

## Gate

Run on commit `db81b807` (the code commit; this section was filled in after
it).

- `uv sync --extra dev` and `uv pip install pypdfium2`: done. `learnloop_mobile`
  is untouched, so no `--extra mobile`.
- `uv run lint-imports --no-cache`: **10 kept, 0 broken**.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`: **7279 passed**,
  0 failed, 14 warnings, 161 s.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`:
  **77 passed**, 7202 deselected, 59 s.
- Frontend (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck`
  clean; `npm test` **74 passed in 18 files**.
- Schema unchanged, so the DB reference scripts were not needed.
- Tracked fixtures: unchanged (`git status` clean after the gate).

## Open questions

1. **LO mastery with nothing assessed.** I chose no mastery step at all, which
   matches the field and the projection ("no evidence"). The alternative is a
   floor-weight EKF step towards the verified answer (the EKF floors the weight
   at 0.1, so zero coverage would still move it upwards). Confirm.
2. **Error events from gate-rescoped attributions.** They still persist, scoped
   `grader_interpretation`, and still show in the feedback's error list, though
   they write no facet evidence. Should the gate drop attributions on
   unverified criteria, or should the feedback hide them?
3. **Diagnoser history.** *(Fixed in the Codex review, F4.)* `diagnosis/split/history.py` still lists an unverified
   criterion that carries no attribution as a failed criterion. S4 then accepts
   a citation to it ("You've made this mistake before"). I left it alone so this
   branch merges cleanly with Slice 2 T1 (recurrence groups). T1 could read
   `grading_support.unverified_criterion_ids` there.
4. **Retention labels.** *(Fixed in the Codex review, F6; the exemption covers PF-c only as the sole review concern since the re-review, F7.)* `outcome_contract.retention_exclusions` still excludes
   any `manual_review` attempt as `unresolved_grade`, which includes PF-c's
   non-blocking log. Exempt `valid_alternative_unverified` (a label-contract
   change)?
5. **`diagnose pfc-report`** computes false rejection from the grader's raw
   score. The learner now gets the assessed score. Add an "applied grade" line
   to the after arm?
6. **A grader that omits a criterion while another is unverified.** The grade
   counts the missing criterion as 0 (the derived score's existing rule), but
   it carries no facet evidence (no assessed row). This is rare (the blind
   prompt asks for every criterion) and left as is.
7. `learnloop show <attempt>` (the CLI inspector) still prints raw points for an
   unverified row. It is owner-facing debug output, not learner feedback.
