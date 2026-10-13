# Learner-text gaps: Codex review fixes

Branch `learner/text-gaps`, worktree `learnanything-text-gaps`. The Codex
adversarial review of `1acf79b2..learner/text-gaps` (head `d5d09238`) raised
16 findings (1 High, 9 Medium, 6 Low). Each was reproduced first (a failing
test where testable), then fixed or rejected. Owner decisions in force
(2026-10-12): recommended defaults accepted; Codex may run every paid role
(estimated cost); the Decider is `perplexity/pplx-decider-v1.1-27b` on
OpenRouter; frictionless defaults (honest labels, generous defaults, live
changes behind kill switches, no shadow stages). Every item of the stage
prompt is an owner decision.

Fix commit: `4cc90153` (code, tests, defaults snapshots, regenerated
references). This file: the commit after it.

## Reproduction

- F1 and F2 reproduced with the reviewer's scratchpad tests on `d5d09238`:
  F1 created `lo_ltg_define_an_eigenvector_*` after the judge raised on the
  true match (`lo_eigen_basics`); F2 finalized both queued texts as
  `unmatched_prerequisite` (`draft_refused: calls exceeds max_calls`, then
  `no llm verdict`) with both jobs `done`.
- `tests/test_learner_text_gaps_review.py` (31 cases) was run against the
  pre-fix source (`git archive d5d09238 src migrations`, pytest's
  `pythonpath` pointed at it): **28 failed, 3 passed**. The 3 that pass on
  both are coverage additions for F13 (a created LO's check passed ->
  maintenance, failed -> learning; the whole pipeline switched off equals
  the predecessor). After the fix: **31 passed**.
- F5 also reproduced live (below): deepseek-chat said `same` to the asking
  item's own LO and to an earlier created LO; the old code would have taken
  the first.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | A missing prerequisite is created when the true match was never judged | fixed | `4cc90153` | `test_f1_a_failed_pair_on_the_true_match_never_creates_and_the_retry_matches`, `test_f1_a_fenced_pair_is_not_a_verdict`; `test_the_queue_runs_a_text_once_retries_failures_and_respects_the_switch` updated |
| F2 | Medium | A spend refusal permanently finalizes an unread text | fixed | `4cc90153` | `test_f2_a_spend_stop_leaves_both_texts_queued_and_stops_the_run`, `test_f2_a_refused_draft_is_deferred_not_logged_unmatched` |
| F3 | Medium | Creation and edge writes are not crash-safe | fixed | `4cc90153` | `test_f3_a_creation_retried_after_a_failed_sync_writes_once_and_is_logged`, `test_f3_a_matched_edge_retried_after_a_failed_sync_is_recorded_and_undoable`, `test_f3_a_belief_candidate_commits_with_its_ledger_row`, `test_f3_a_sighting_is_counted_once_across_a_retry`, `test_f3_a_job_that_gives_up_after_writing_names_the_creation_and_the_owner_can_undo_it` |
| F4 | Medium | With no asking subject, candidates are vault-wide | fixed | `4cc90153` | `test_f4_without_a_grounded_subject_only_the_anchors_are_judged_and_nothing_is_created` |
| F5 | Medium | Several `same` verdicts: the first in list order (often the item's own LO) wins | fixed | `4cc90153` | `test_f5_several_same_verdicts_are_ambiguous_and_target_nothing`, `test_f5_a_match_on_the_items_own_lo_is_no_prerequisite_target`; live run below |
| F6 | Medium | Gap targets back-dated to question time (look-ahead) | fixed | `4cc90153` | `test_f6_a_question_retargeted_by_a_later_reading_is_observed_at_the_reading` |
| F7 | Medium | The seed auto-applies on the asking LO's sources passed off as grounding | fixed | `4cc90153` | `test_a_missing_prerequisite_is_drafted_created_live_seeded_and_committed` now asserts `review_required` |
| F8 | Medium | Stuck answers queued only after a completed live split diagnosis | fixed | `4cc90153` | `test_f8_a_stuck_answer_is_queued_at_recording_without_a_diagnosis`, `test_f8_the_adapter_reads_the_marker_before_scanning`, `test_f8_a_diagnosis_no_longer_scans_stuck_answers` |
| F9 | Medium | Undo taps and owner reversals never reach `judgment_ledger` | fixed | `4cc90153` | `test_f9_undoing_an_edge_or_a_creation_is_a_ledger_verdict`, `test_f9_an_owner_not_what_i_meant_is_an_owner_verdict` |
| F10 | Medium | `add_edges_enabled` is not a working kill switch; cycle check is TOCTOU | fixed | `4cc90153` | `test_f10_switching_edges_off_removes_their_effect_and_keeps_them_in_the_file`, `test_f10_a_creations_edge_follows_the_creation_switch`, `test_f10_the_cycle_is_rechecked_on_the_file_inside_the_lock` |
| F11 | Low | The report cannot answer "Decider or LLM" on outcomes | fixed | `4cc90153` | `test_f11_first_checks_per_chooser_survive_the_creation_switch_and_since_windows_everything`, `test_f11_pair_agreement_honours_since` |
| F12 | Low | No aggregate live spend cap; seed unit billed to the wrong route | fixed | `4cc90153` | `test_f12_the_live_daily_cap_defers_to_the_next_day_without_using_a_retry`, `test_f12_the_daily_cap_counts_the_pipelines_receipts`, `test_f12_the_seed_unit_is_admitted_on_a_metered_tutor_route` |
| F13 | Low | Tests miss the failure paths | fixed | `4cc90153` | the 31 cases above, plus `test_f13_a_created_los_check_passed_goes_to_maintenance`, `test_f13_a_created_los_check_failed_goes_to_learning`, `test_f13_the_pipeline_switched_off_queues_exactly_as_the_predecessor_version` |
| F14 | Low | A stuck attempt can be counted two or three times | fixed (in this branch's scope) | `4cc90153` | `test_f14_a_stuck_answer_and_its_diagnosis_give_one_observation`; main's `stuck_confusion` is a merge-time item (below) |
| F15 | Low | Privacy: raw learner text goes to OpenRouter by default | fixed (disclosed); behaviour change rejected | this commit | Owner section below. Leaving the diagnosis source out of the Decider's kind call is rejected: with `chooser = "decider"` the Decider is the authoritative kind for every source, so dropping it would silently change the chooser's meaning; the owner chose the Decider and accepted text leaving the machine for OpenRouter embeddings |
| F16 | Low | Label/migration collide with main; a missing edge reloads every poll | fixed (reload); relabel deferred to merge | `4cc90153` | `test_f16_a_removed_edge_reloads_once_and_bumps_nothing`. Relabel rejected for now: the stage notes say to take the next free label and migration number at landing and expect relabelling; this branch cannot rebase onto main (`mvp-0.13` and 178 are main's stuck prompt now), so the label stays `mvp-0.13` and the migration 177 until the merge renumbers both |

## What changed, per finding

- **F1 (High).** `pipeline._judge_all` keeps only settled verdicts (status
  `judged` or `already_judged` with a verdict; a `fenced` pair's verdict was
  never appended and does not count). `_require_settled` raises
  `ReadingDeferred` when the authoritative judge left any candidate pair
  without a verdict (failed, claimed elsewhere, fenced); no ledger row is
  written and the job retries with backoff, then logs `failed` with no
  target. The same rule guards beliefs (a failed pair could be the true
  match, and a new candidate would duplicate it). A missing judge route still
  finalizes as `unmatched_prerequisite` (`no llm judge`), honestly.
- **F2.** Any spend refusal or cancellation before the text's action is
  decided raises `ReadingDeferred(spend=True)`: a `not_run` pair of either
  judge, the query embedding, the Decider's kind, the stuck-text reading,
  "needed?" and the draft. Under a command's shared budget (`gaps run`) the
  job is released with its attempt refunded (`release_job(refund_attempt=True)`)
  and the run stops (new job state `deferred`); the next run reuses every
  paid verdict. On the live path (one budget per text) it is a retry like any
  failure. The seed item, optional content made after a creation is written,
  still records `refused` rather than holding back a finished reading.
- **F3.** Ids derive from the learner text: `edge_ltg_<hash(text, prerequisite, dependent)>`,
  `lo_ltg_<slug>_<hash(text)>`, `<concept slug>_<hash(text)>`. The draft and
  these ids are checkpointed in the job payload BEFORE anything is written;
  a retry with a draft in progress finishes the creation without re-judging
  (re-judging could see the half-written LO and orphan it). The matched edge
  is checkpointed (id and "needed?" verdicts) before it is written; a retry
  finds it. `write_created_prerequisite` and `add_prerequisite_edge` look
  each entity up first, so they are idempotent. A holding-pen candidate or a
  sighting's occurrence now commits inside the ledger row's transaction
  (`ActionOutcome.writes`). A job that gives up names what its attempts
  wrote on the `failed` row (`created_learning_object_id`, `edge_id`), which
  counts toward the daily creation cap and takes `undo_creation` /
  `undo_edge` (`learnloop gaps undo`).
- **F4.** Without a grounded subject, `prerequisite_candidates` returns the
  text's own anchors only (no declared, no created-today, no vault-wide
  shortlist) and nothing is created (`unmatched_prerequisite`, reason
  `no_subject`): only a grounded subject was searched for duplicates.
  `subject_for_creation` no longer infers a subject from the shortlist. The
  belief kNN pool also needs a subject. This is stricter than the finding's
  "allow only creation-subject inference": a subject inferred from anchors
  that span two subjects would be arbitrary, and no duplicate check ran in it.
- **F5.** Two or more `same` verdicts: `unmatched_prerequisite`, reason
  `ambiguous`, the ids in `detail.same` (listed in the report's batch
  review). One `same` on the asking item's own LO: `unmatched_prerequisite`,
  reason `own_learning_object`: no target, no signal, no edge, no sooner
  check. Beliefs with two or more `same`: `unplaced`, reason `ambiguous`.
- **F6.** A question retargeted by its gap is observed at
  `max(question time, gap created_at)`; `SIGNAL_VERSION` is
  `interaction-signals-v2`.
- **F7.** The asking LO's notes are no longer passed as the seed's
  grounding; `tutor/promotions.py` is back to `1acf79b2` (the parameter had
  no other user). The promotion path's own rule sends the seed to review
  (`review_required`, "its practice item is waiting for review"); its light
  commitment is still written and its check is served once the owner
  accepts the item. Owner question 1 below.
- **F8.** `enqueue_post_attempt_learner_text` (in `diagnosis/followups.py`,
  called by `run_post_attempt_pipeline` after the completion commits) queues
  every non-empty stuck answer when it is recorded: graded right or wrong,
  diagnosed or not, split on or off. `StuckTextSource` gains an optional
  per-attempt `stuck_text(connection, attempt_id)`; the default adapter reads
  the stuck marker (`practice_attempts.declared_stuck`) for that one attempt
  before it ever calls `stuck_answers()`, so an ordinary answer scans
  nothing. `enqueue_after_diagnosis` no longer rescans stuck answers.
  Integration point at merge: main's `attempts.stuck.stuck_answers` and its
  `declared_stuck` column (migration 178) are what the adapter reads; no
  code change.
- **F9.** `reverse_gap` appends, in the reversal's transaction, a `no` on
  `prerequisite_needed` for `undo_edge` (left: the matched LO) and
  `undo_creation` (left: the created LO); right: the practice item, else the
  learner text. Judge `learner_card` for the learner's tap, `owner` for
  `learnloop gaps undo` (the owner). "Not what I meant" by the owner is now an
  `owner` verdict. An undo does not add a `different` on `same_prerequisite`:
  removing a link says the link is wrong ("link undone", the match label
  stays), not that the match is.
- **F10.** `vault.lifecycle.learner_text_gap_edge_in_effect` keeps a
  learner-text gap edge out of the loaded vault while its switch is off: a
  match edge needs `add_edges_enabled`, a creation edge
  (`provenance.origin = "creation"`, new) needs `create_prerequisites_enabled`,
  both need `enabled`. The loader filters once, so placement order, the F11
  declared-prerequisite mapping, the diagnoser's neighbourhood and the map
  all see the predecessor's graph; the edge stays in `concepts/relations.yaml`
  and returns when the switch does. `add_prerequisite_edge` reloads the vault
  inside the vault lock and re-checks the cycle on the relations file as it
  is then (including switched-off gap edges).
- **F11.** Commitments are read whatever the creation switch says; first
  checks are given overall and per chooser (`by_chooser`); `--since` windows
  readings, reversals, pair verdicts, commitments and jobs; the diagnosis
  card's `same_cause` `learner_card` "not the same mistake" taps on answers
  this pipeline read as beliefs are counted.
- **F12.** `learner_text_gaps.max_calls_per_day = 500` (parameter registry:
  structural/operational): before each text on the live path the pipeline's
  logical calls since UTC midnight are counted from its receipts
  (`model_call_receipts`, owner `learner_text_gap`); at the cap the job is
  released, attempt refunded, until the next UTC day (overshoot at most one
  text's `max_calls_per_text`). `gaps run` keeps its own command caps. The
  seed unit is admitted on the costlier metered route of `tutor_qa` and
  `authoring` (an unpriced metered route first, so it fails closed).
- **F14.** One learner-gap observation per attempt: the first read (its stuck
  text or its diagnosis), which keeps the availability contract. Main's
  `stuck_confusion` signal targets the item's own LO and does not exist on
  this branch; whether a stuck answer may carry both is a merge-time
  integration point (owner question 3).
- **F16.** `get_learner_text_gap` reloads at most once per reading state
  (gap id and its reversals) and bumps the queue revision only when the
  reload made the vault match; an edge removed in the graph editor or kept
  out by its switch no longer reloads on every poll.

Defaults snapshots were recomputed for every version (the new leaf);
`mvp-0.13`: `f8555cfa…9bbac`. Config and DB references regenerated
(658 effective leaves).

## Live run (paid, on a backup copy)

On `fixtures-local/ltg-la` (the backup-API copy from the first round; the
tracked vaults were never touched). Dry run first (`gaps run --dry-run`:
1 queued, ceiling 30 calls / $0.25; the plan now shows the live daily cap,
129 calls today). One tutor question on `lo_compute_with_complex_numbers`
("How do I multiply (2+i)(3-4i)? I keep forgetting how to expand two
brackets."), then `gaps run --max-texts 1 --max-calls 30 --max-cost-usd 0.10`.

| What | Model | Calls | Tokens in / out | Cost |
|---|---|---|---|---|
| tutor answer (named the gap) | deepseek/deepseek-chat | 1 | 3,783 / 259 | about $0.0013 (estimate) |
| query embedding | qwen/qwen3-embedding-8b | 1 | 40 | $0.0000004 |
| kind + 8 pairs (Decider) | pplx-decider-v1.1-27b | 9 | 4,275 / 9 | $0.0000855 |
| 8 pairs (LLM judge) | deepseek/deepseek-chat | 8 | 3,912 / 366 | $0.0014 |

About $0.003 in all (18 pipeline calls receipted). Result: `ambiguous`. The
LLM judge said `same` to the item's own LO and to `lo_ltg_expand_products_of_binomials_…`
(created earlier the same day); the Decider said `same` only to the item's
own LO. Before the fix this matched the first in order (the item's own LO,
F5); now nothing is targeted and the reading is listed for batch review.

## Owner section

- **Privacy (F15).** With the defaults, the learner's own words leave the
  machine to OpenRouter: the Decider's kind call (`learner_gap_decider`,
  `perplexity/pplx-decider-v1.1-27b`) receives the raw text of every tutor
  question, every stuck answer and, for the diagnosis source, the wrong
  answer itself, with the item's prompt and LO titles; the Decider's pair and
  "needed?" calls receive the named gap and LO statements, not the raw text.
  With embeddings on, the named gap (not the raw text) goes to the embedding
  model. Codex (the judge, reader and draft by default) runs on the owner's
  ChatGPT subscription. To keep learner text local, set
  `[learner_text_gaps] decider_enabled = false` (the chooser must then stay
  `context_model`).
- **Open questions.**
  1. Seeds now go to review (F7). Accept that, or name an authoritative
     source for created prerequisites (for example: the seed auto-applies
     when the tutor's answer note is accepted as grounding)?
  2. `max_calls_per_day = 500` on the live path (the diagnoser's default).
  3. At merge with `practice/stuck-prompt`: may a stuck answer carry both
     main's `stuck_confusion` (the item's own LO) and one learner-gap
     prerequisite observation (another LO)? Today they target different LOs.
  4. A text whose anchors span two subjects creates nothing (F4); a reader
     question citing LOs in two subjects is the usual case. Keep?
- **Merge.** Relabel `mvp-0.13` to the next free successor after main's
  (main's stuck prompt is `mvp-0.13`), rename `upgrade_to_mvp013`, recompute
  the snapshot, and renumber migration 177 (T6 has 177, the stuck prompt
  178).

## Gate

Run on `4cc90153`, `TMPDIR` in the gitignored `fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | OK |
| `uv run lint-imports --no-cache` | **12 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8238 passed**, 0 failed (46 warnings), 254 s (8207 before + 31 new) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **87 passed**, 8151 deselected, 90 s |
| `db_generate_reference.py` then `db_validate_reference.py` | `errors: []` (schema 177 unchanged, 302 table notes, 658 config leaves; the prose counts in `Configuration.md` and `Database.md` updated by hand) |
| `validate_vault.py` (extra) | passed (1,073 notes) |
| Frontend | not changed in this fix step (not run) |
| Targeted before the gate | `test_learner_text_gaps*.py`, `test_config_refactor.py` and 37 related files: 898 passed |

## Re-review (round 2)

The Codex re-review of `c3d703cd` confirmed the only High (round 1 F1: a
missing prerequisite created when the true match was never judged) as
**fixed**, and reopened the stage on two new Medium defects the fixes
introduced, plus five Lows. Their ids below are the re-review's own
(RR-F1 to RR-F7). Each was reproduced on `c3d703cd` before it was fixed.
Fix commit: `1f3606cc` (code and tests); `6699a29f` regenerates the
references (anchors and stamps only); this file is the commit after them.

### Reproduction

- RR-F1 and RR-F2: the reviewer's scratch repros (`test_repro_round2.py`,
  `test_repro_f6.py`) pass on `c3d703cd`, so the defects are present. The
  retry's row is `('none', None, None)` while
  `lo_ltg_define_an_eigenvector_190dd6f6` and its edge stay on disk. A gap
  read three days later adds `('question_event:q1:assistance',
  '2026-05-19T12:00:00Z', True)`.
- RR-F1 (the other paths) and RR-F5, with scratch repros that run on
  `c3d703cd` (`scratchpad/repro3/test_base_defects.py`):
  - A matched edge written before a failed sync, then the chooser switched
    to `decider`: the retry logs `('none', None, None)` and the edge stays
    on disk with no row. With the chooser unchanged the edge survives,
    because the ledger's standing verdicts are reused.
  - `enabled` switched off after a creation was written: the job ends
    `skipped`, the LO is on disk, and there is no row.
  - After one `gaps run`-style shared-budget text, `calls_today` is 3.
- The new `tests/test_learner_text_gaps_rereview.py` (19 cases) run against
  the `c3d703cd` source (`git archive`, pytest's `pythonpath` pointed at
  it): **18 failed, 1 passed**. The one that passes on both is a guard: a
  job switched off before any write is still `skipped`.
  - RR-F2, RR-F3, RR-F4, RR-F6 and RR-F7 fail on the defect itself.
  - The RR-F1 and RR-F5 cases fail there on the new names (`retry_later`,
    `TextBudget.for_command`) before they reach the defect. That is why
    the scratch repros above were written.
- After the fix: **19 passed**, and the round-1 file still passes 31/31.
- RR-F7 was also checked on the round-1 backup copy
  `fixtures-local/ltg-la` (read-only, no call). Its two pre-fix edges carry
  no `origin`, and both are now classified `creation`. The copy's ledger
  agrees: both are `created_prerequisite` rows.

### Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 (round 1) | High | Missing prerequisite created when the true match was never judged | confirmed fixed by the re-review | `4cc90153` | no change this round |
| RR-F1 | Medium | A retry reads a stuck answer again, so a different or failed reading orphans a half-written creation or edge | fixed | `1f3606cc` | `test_rr_f1_a_stuck_retry_finishes_the_recorded_creation_whatever_the_second_reading` (4 cases: second reading `none`/failed, with and without round-1-shaped progress), `test_rr_f1_a_recorded_edge_is_finished_after_the_judges_the_chooser_and_the_switch_change`, `test_rr_f1_a_job_stopped_after_a_write_logs_the_write_as_failed_and_undoable` (switched off, text gone), `test_rr_f1_a_job_switched_off_before_any_write_is_still_skipped` |
| RR-F2 | Medium | The F6 fix is incomplete: a gap read later still sets question-time "help before work" | fixed | `1f3606cc` | `test_rr_f2_a_gap_read_later_adds_no_question_time_assistance` |
| RR-F3 | Low | One failed judge pair stops the whole drain | fixed | `1f3606cc` | `test_rr_f3_a_failed_pair_backs_off_one_text_and_the_run_goes_on` (live and command budgets), `test_rr_f3_the_sidecar_drain_goes_on_past_a_text_backing_off`; round-1 tests now expect `retry_later` |
| RR-F4 | Low | The "no full scan" claim holds only for answers that are not stuck | fixed | `1f3606cc` | `test_rr_f4_a_stuck_answer_is_read_by_its_id_with_its_current_reading`, `test_rr_f4_the_stuck_modules_own_per_attempt_reader_is_preferred`; `test_f8_the_adapter_reads_the_marker_before_scanning` now asserts `scans == []` |
| RR-F5 | Low | The live daily cap counts CLI spend | fixed | `1f3606cc` | `test_rr_f5_a_commands_calls_do_not_count_toward_the_live_daily_cap`, `test_rr_f5_gaps_run_reads_on_a_command_budget` |
| RR-F6 | Low | The report overcounts "not the same mistake" taps | fixed | `1f3606cc` | `test_rr_f6_only_a_tap_on_a_belief_answer_is_counted` |
| RR-F7 | Low | Edges written before the fix are switched by the wrong setting | fixed | `1f3606cc` | `test_rr_f7_an_edge_without_a_recorded_origin_follows_its_own_switch` (both switches); the backup-copy check above |

### What changed, per finding

- **RR-F1.** The job progress now records the decision as well as the
  writes, and a retry finishes the writes first.
  - **The decision is recorded once.** `pipeline._decide` checkpoints
    `decided` (the reading, the Decider's kind, the chooser and the
    authoritative kind) before anything acts on it, and every retry reuses
    it. A stuck-text reading is also checkpointed as soon as it is read
    (`reading`), so a refused Decider does not cause a second paid reading.
    `GapReading.as_progress()` and `from_progress()` round-trip the reading.
  - **Recorded writes are finished first.** Before dispatching,
    `pipeline._resume` finishes a recorded creation (`created.draft`) or a
    recorded matched edge (`edge.edge_id`). It does this whatever the new
    reading, the chooser or the creation and edge switches say, and without
    judging, asking or reading again. The row is logged `kind =
    prerequisite` with `detail.resumed`.
  - **The edge checkpoint carries its match.** It now holds the match's
    target subject, basis and detail, so a resumed edge logs the same match.
  - **Progress from round 1 is covered.** Progress without `decided` still
    resumes from its `created` or `edge` entry.
  - **A stopped job still gets a row.** A job switched off (`enabled =
    false`), or whose text is gone, after an attempt wrote to the vault is
    logged `failed` with `failed_row(progress=...)` and the job ends
    `failed`. No paid call finishes it while the switch is off. The daily
    creation cap counts it, and `learnloop gaps undo` reaches it. A job
    that recorded ids but wrote nothing is still `skipped`.
- **RR-F2.** `field/signals.py` computes `logged_before`, the
  `practice_assistance` row's `help_before_work`, from the logged
  `question_type` before the gap override. The gap still retargets the
  question's own signal, observed when the gap was read (round-1 F6). No
  new `SIGNAL_VERSION`: `interaction-signals-v2` is this branch's own label
  and is not on main yet.
- **RR-F3.** A single text that backs off is now `retry_later` (it was
  `released`). `run_pending` (`gaps run`) and the sidecar's gap drain keep
  going past it and stop only on `deferred` (a spend stop or the daily cap)
  or `lease_lost`. The backoff's `not_before` keeps the same job from being
  leased again in the same drain.
- **RR-F4.** `StuckAnswersAdapter.stuck_text` reads one attempt by its id.
  - It uses the stuck module's per-attempt `stuck_answer(connection,
    attempt_id)` when the module has one.
  - Otherwise it reads the `declared_stuck` row from `practice_attempts`
    with the reading `stuck_answers` would return: the current, unsuperseded
    `stuck_reading` verdict in `judgment_ledger`, else the latest blind
    record's `stuck_reading`.
  - It never scans every stuck answer, so queueing is O(1) per answer.
  - Main's `stuck_answers` has no per-attempt form, and this branch cannot
    add one to a module only main has. Merge item below.
- **RR-F5.** `TextBudget` gains `owner_kind`. `TextBudget.for_command`,
  which `learnloop gaps run` now uses, receipts its calls as
  `learner_text_gap_command`. The live daily cap
  (`store.pipeline_calls_since`) counts only `learner_text_gap`, the live
  path's receipts. The `max_calls_per_day` schema comment says so.
- **RR-F6.** `report._card_taps` counts a `same_cause` `learner_card`
  `different` tap only when its `left` (the tapped answer) is an answer
  this pipeline read as a belief. T1's `diagnosis/split/card.py` writes
  `left` = the tapped attempt and `right` = the cited one.
- **RR-F7.** The edge's origin is inferred, with no backfill or vault write.
  - `vault.lifecycle.learner_text_gap_edge_origin` gives an edge without a
    recorded `origin` the origin `creation` when its prerequisite concept
    is the concept the same learner text created. The created LO's
    provenance names that text (`learner_text`). Otherwise the origin is
    `match`.
  - `load_vault` now filters relation edges after the LOs are loaded,
    since nothing between the two reads `loaded.edges`.

### Merge notes (in addition to round 1's)

- **Stuck answers.** At merge with `practice/stuck-prompt`, consider adding
  `stuck_answer(connection, attempt_id)` to `attempts.stuck`. The adapter
  then uses it with no code change. Until then the adapter's per-attempt
  query mirrors `stuck_answers`' choice of reading, and the two must stay
  in step.
- **Interface changes.** `gaps run --json` outcomes say `retry_later`
  where they said `released`; no UI reads it. Command receipts have owner
  kind `learner_text_gap_command`.

### Live run

None this round: every finding is deterministic control flow and is
covered with fakes. The RR-F7 check on `fixtures-local/ltg-la` made no
call. **No paid calls, $0.**

### Gate (re-review)

Run on `6699a29f` (the fix `1f3606cc` plus its regenerated references),
with `TMPDIR` in the gitignored `fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | OK |
| `uv run lint-imports --no-cache` | **12 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8257 passed**, 0 failed (46 warnings), 300 s (8238 in round 1 plus the 19 new cases) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **87 passed**, 8170 deselected, 78 s |
| `db_generate_reference.py` then `db_validate_reference.py` | `errors: []`. The DB schema is unchanged (177); one config schema comment changed, so the references were regenerated (stamps and line anchors only). |
| Frontend | not changed (not run) |
| Mobile allowlist | no new sidecar RPC |
| Targeted before the gate | `test_learner_text_gaps.py`, `_flow.py`, `_review.py` and `_rereview.py`: **92 passed** |
