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
