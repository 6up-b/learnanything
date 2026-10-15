# Diagnosis input provenance: every model-written text records what it was written from

**Stage:** `diagnosis-input-provenance`, branch `diagnosis/input-provenance` (worktree `learnanything-merge`),
base `499bd3ebd` (main, mvp-0.25, with the chat frontend's C1a and migration 203).
**Code:** `1e36c399c` (the build) and `060645417` (the first gate's six failures, two fail-closed hardenings, the
reference). **Migration:** 204. **Spec:** [spec_mcp_frontend_c1.md](../specs/spec_mcp_frontend_c1.md)
§4.6, §4.7 rule 1 (c) and §4.8 (rewritten as built).
**Earlier records:** [mcp-c1a-narrow.md](mcp-c1a-narrow.md) (the narrow rule and the queued follow-up),
[mcp-c1a-narrow-codex-review.md](mcp-c1a-narrow-codex-review.md).
**Codex review:** [diagnosis-input-provenance-codex-review.md](diagnosis-input-provenance-codex-review.md)
(F1–F4 fixed, F5 fixed in part; this record is annotated in italics where the review showed a claim did
not hold).

## Why: the owner's decision (2026-10-14, "land narrow, then fix source")

C1a landed with a narrow rule: everything a model wrote (misconception and candidate statements and
corrections, hypothesis and recurrence statements, diagnosis summaries, gap targets, a question's words,
generated topic names) was held back, because five reviews in a row found inputs no record named (a
snapshot diagnosis's whole-vault reads, a joint grader's C4 receipt written outside the grading transaction,
a generated topic's title). Its rule (c) was a hook: a derived text with a complete, recorded write-time
provenance whose inputs are all safe may be shown. **No producer wrote a record.** This stage makes every
writer record its inputs at the source, in the transaction that writes the text, so (c) can release the prose.
Nothing is inferred from the output.

## The record

One append-only table, `text_write_provenance` (RAW_LEDGER, append-only by trigger;
`src/learnloop/db/stores/write_provenance.py`). A row names the text (`kind`, `record_id`), the hash of the
text as written, the writer, and the **closed** record of what it read: its own reads plus the recorded inputs
of every derived text it read (folded at write time, so a reader never chases a chain).

| Input | Meaning |
|---|---|
| `answers` | Learner answers read (their text, or a grader's output about them), each with the contract revision it was read under (`None`: no single pinned contract on its own item) |
| `items` | Items whose question (or key, through an answer) was read: their protection is checked and their keys filter the text |
| `solution_items` | Items whose rubric or reference solution was read, directly or through a grader's output |
| `topics` | Topics whose names or ids were read (a generated one only with its own record folded in) |
| `sources` | Source refs whose text was read (a facet claim's passages, a Reader passage) |
| `questions` | Learner questions read, each with the contract it was asked about (Q10) |
| `complete`, `incomplete_reasons` | The writer's statement that nothing else was read, and what it could not account for |

A text's provenance is the union of every row written for it (each writer of the text). It is held back when
there is no row (every row written before this stage), when a row is incomplete, or when the latest row's hash
no longer matches the text as stored (a writer that recorded nothing rewrote it).

## Who records what

| Writer | Kind | What it records | Where |
|---|---|---|---|
| Blind grader (live, regrade) | `grading` | The answer under its pinned contract, the item (question, rubric, reference solution), its topic | `attempts/attempts.py` (`_complete_blind_graded_attempt`), `attempts/regrade.py` |
| Joint grader | `grading` | The same plus the prior answers it was shown (C4). **Q14:** the grade, the Phase-C receipt and this record commit in one transaction | `attempts/attempts.py` (`_complete_joint_graded_attempt`, `_record_diagnostic_augmentation`) |
| An older grading (no row) | — | Accounted for by its own ledger: a blind record (learner-blind by construction), a model-free grade (no grader text), a joint grade with a C4 receipt; a joint model grade without one is **incomplete** | `write_provenance.grading_record` |
| Diagnoser | `diagnosis` | Every attempt its context showed (with the grading folded in, and the item's solution counted as read, when a grader's output about it was shown), the diagnosed item's rubric and reference solution, the neighbourhood's topics, every prior hypothesis, registry statement, repair and unresolved-cause factor read (their records folded in, each checked against the text it showed). *Codex review F3: the record was closed at persistence, after the model ran, so a regrade meanwhile could certify a grading the diagnoser never saw. It is now frozen when the context is built (`provenance.frozen_record`), with each grading's mark checked against what the history store read. F2: a generated topic's record is folded only when it covers the title the context showed* | `diagnosis/split/provenance.py`, `context.py`, `diagnoser.py`, `jobs.py` (`_persist` → `record_diagnosis_reads`, in the diagnosis's transaction, the record frozen before the model call) |
| Diagnoser, snapshot mode | `diagnosis` | The export entries the transport's reported reads served: a plain read (`cat`, `head`, `tail`, `sed -n` with a print-only script, `nl`, `less`, `more`, `wc`) serves its file; `ls`/`cd`/`pwd` names only (export file names are opaque ids); any other report (a search, a glob, a pipe, a script, another `sed` script, a turn item the transport could not read) counts as the **whole export**; a path outside the export, or no report at all, makes the record **incomplete**. The receipt keeps what was served (`snapshot.served`). *Codex review F1: a single `&` slipped through (`ls & cat <file>` counted as names only). Only one strictly validated simple command is accounted for now (`provenance.simple_command`: no shell syntax outside single quotes), with output-only options; anything else counts as the whole export* | `provenance.snapshot_reads`, `served_entries`, `snapshot_record`; `snapshot.py` (each export file's entry and its record, frozen when written) |
| Hypothesis materialization | `hypothesis` | The attempt's grading and the diagnosis whose causal view lies over the event; a factor's candidate: every completed diagnosis of the attempt | `causal_attribution._statement_provenance` |
| A hypothesis version keeping its head's statement | `hypothesis` | The head's record, carried forward | `Repository.append_causal_hypothesis` |
| Candidates: error hunt, gap reader, a confirmed factor | `candidate` | The hunt's grading (the grading in progress, `grading_in_progress`), the reading's writer, the factor's attempt | `error_hunt.py`, `text_gaps/actions.py`, `causal_attribution.py` |
| Promotion, legacy normalizer | `misconception` | The candidate's (or projected hypothesis's) record; the event's grading and diagnosis | `misconceptions.py` |
| Correction frozen from facet claims | `misconception_correction` | The topic and the source refs the facets were authored from | `misconceptions._promotion_provenance` |
| A rewritten statement or correction | same | Its own record when the caller passes one (`statement_provenance`); otherwise the hash check holds the text back | `Repository.update_misconception` |
| Gap reader, a question's words | `learner_text_gap` | The question with its contract (Q10), its item, the attempt it was asked during, a Reader question's passage and, when the learner could have seen the solution first (a feedback question, or a reveal of the item before it), the solution and the grading | `text_gaps/provenance.question_record`, `pipeline._record_written_texts` |
| Prerequisite drafter | `learning_object` | The reading's writer, the learner text and its context, the asking topic, and the concept titles of the subject it was shown (kept in the job's progress, so a resumed creation records the same). *Codex review F2: each generated topic's record is folded only when it covers the name the drafter was shown (a concept title, the asking topic's title, the named prerequisite); the record is built before the draft call* | `text_gaps/provenance.drafter_record`, `pipeline._create` |
| Seeded item | `practice_item` | The drafter's record plus the tutor's (incomplete, below) | `pipeline._record_written_texts` |
| A tutor question's reading (belief statement, prerequisite name) | — | **Incomplete:** the tutor's own inputs (thread, expected answer, feedback, passages) are not recorded yet | `text_gaps/provenance.reading_record` |

**Q9:** `error_event_lineage` (RAW_LEDGER, append-only): a regrade's re-minted error events record every id they
replace, in the regrade's transaction. *Codex review F4: a regrade that found no error minted nothing, so
nothing was recorded and the retired ids lost their answer. Each retired id is now recorded with no
replacement (`error_event_id` NULL, "no current error"; `retired_error_event_ids`).* `current_error_event_ids` resolves a listed id to the events that stand for
it now, and the diagnosis history (`VaultHistoryStore`) resolves a replaced id to its answer, so a belief listing
it keeps its source attempt. **Q10:** `question_events.assessment_contract_version_id`: the tutor names the item as
presented mid-attempt (`snapshot_for_presentation`, content-addressed); for a question about a graded attempt the
repository records the attempt's pinned contract; NULL on no item and on every question written before.

## The check (rule (c), `learner_context.TextGuard.derived`)

A text is released only when its record is complete, covers the text as stored, and every input passes the shared
protection (`learner_protection`; the router card is unchanged and may read the same records):

1. the entry's own answers and items, and every recorded item: not exam, held-out, reserved, cold or a probe;
2. every topic authored, or generated with its own record folded in;
3. every answer: (b)'s checks (protection, keys readable, states no key its item had, one pinned contract), and
   read under the revision it is pinned to now (`REVISION_CHANGED_BEHIND` otherwise);
4. every question: on record, its item unprotected, recording a contract of that item (`QUESTION_UNRECORDED`);
5. every source ref: not exam or held-out material (`exam_material.source_ref_protected`);
6. every item whose rubric or reference solution was read: **its attempt window closed** (its latest answer is
   correct and not held: the retrieval policy's rule for unlocking an item's own solution, `PastWork.solution_reason`;
   the threshold is pinned to `instructional.policy.WINDOW_CLOSING_CORRECTNESS` by a test). Otherwise
   "written with the worked solution of a question you can still answer";
7. the text reproduces no key of any item or topic named.

The kill switch `diagnosis.chat_shows_recorded_text` (on) puts back the narrow rule (nothing derived shown).

## Persisted meaning: no successor, and why

`docs/algorithm-change-playbook.md` governs changes to persisted meaning (scoring, scheduling, projections).
None changes here, so there is no algorithm successor:

*Codex review F5: "only a read-model change" does not by itself answer handoff §0 rule 5 ("a change to what
is served is an algorithm successor with a kill switch"). The successor is rejected under the owner's
standing ruling (live changes behind kill switches, not successors, for serving changes replay never reads),
as for plan determinism, exam protection and the reading step; the review step added the validation the
ruling requires: switch-off parity with C1a's code, shadow rebuilds, and replay tests. See the review record.*

- **Grading.** The graders' prompts, contexts and output handling are unchanged, and a successful grading
  writes the same rows as before, plus one `text_write_provenance` row. Q14 changes only a failure path. A
  Phase-C receipt that could not be written used to be swallowed after the grade had committed, leaving a
  joint grade with no receipt. It now fails the grading, and the door's existing fallback (the learner's
  self-grade, as for any grading failure) commits instead. That boundary was `pragma: no cover`; no receipt
  failure is on record.
- **Scoring, scheduling, replay.** Both new tables are RAW_LEDGER. Replay never reads or clears them (the
  table-role tests pin this). *Codex review: not as built. Replay re-materializes causal episodes, and
  `materialize_causal_episode` built each hypothesis's record before the identical-version check, so a
  rebuild read the records (it wrote none). The record is now built only when a new version is appended:
  an idempotent rebuild neither reads nor writes one (`test_f5_replay_never_reads_the_switch_or_the_records`);
  a regrade's replay that appends a changed version records it, as any writer does.* `error_event_lineage` is written after the regrade's replay, in its
  transaction. Only the diagnosis history reads it, to name a belief's source attempt where a replaced id
  used to resolve to nothing. That changes what a later diagnosis context can name, not any score or
  schedule.
- **Q10.** A nullable column, written for new questions and read only by the chat guard. Recording a
  mid-attempt question's contract calls `snapshot_for_presentation`, which is content-addressed and
  idempotent, the same call the sidecar makes when it presents the item.
- **What learners see in chat** changes. That change sits behind the kill switch
  `diagnosis.chat_shows_recorded_text` (on, per the owner's "live changes behind kill switches"). Off, it
  puts back the C1a narrow rule. The writers record either way.

## This round: the first gate's failures and two fail-closed hardenings

The first full run on `1e36c399c` (`fixtures-local/dip-fullsuite-1.log`) had **6 failed, 11,675 passed**. Fixed:

1. **Three tests used a failing Phase-C receipt as a stand-in for "a later step fails after the grade
   committed"**:
   - `test_attempt_completion::test_committed_model_grade_keeps_its_provenance_through_recovery`;
   - `test_tui_feedback::test_committed_model_grade_is_not_regraded_when_a_later_step_fails`;
   - `test_tui_retry_resumes_a_committed_grade_instead_of_recording_another[auto_grade, dont_know]`.

   Q14 put that receipt inside the grading transaction, so the stand-in became "the grade rolls back and the
   door self-grades". The tests now use `fail_after_the_joint_grade_commits` (in
   `tests/test_diagnostic_augmentation.py`), which raises once the joint grade has committed. They keep the
   invariant they cover: a committed model grade is resumed, never regraded or self-graded. The new
   behaviour of a failing receipt is pinned by `test_a_receipt_that_cannot_be_written_commits_no_augmented_grade`.
2. **The function-local import ratchet.** `tutor_qa` imported `snapshot_for_presentation` inside a function.
   It is now a module-level import, so no frozen edge is added.
3. **The SQL-owner registry.** `db/stores/write_provenance.py` is registered as an owner (its two inserts).

Two fail-closed hardenings came out of re-reading the snapshot path:

- **The transport's report.** `ai.providers.codex._workspace_activity` collected `command` / `path` /
  `file_path` from the turn's items and silently skipped anything else. A tool item of another shape, or a
  typed SDK item wrapped in a root model, would have made a whole-export read look like "opened nothing".
  It now unwraps root models and reports every item that is not text-only and names no command or path as
  `unaccounted turn item: <type>`. The record counts that report as reading the whole export. The isolated
  turn already turns off MCP, web search and image view, so this is defence in depth.
- **`sed`.** Only a print script (`3p`, `1,40p`, `$p`) is accounted as reading its file. Any other script
  counts as the whole export: GNU `sed`'s `e` command runs a program, and `w` writes.

The receipt's `snapshot.served` now lists paths only for an `entries` read. For `whole` and `outside` it
keeps a count, so a large vault's receipt stays small. The DB/config reference was regenerated for the two
new tables and the new config leaf (858 leaves, 323 table notes; the prose counts were updated by hand).

## Fail first

The base tree (`git archive 499bd3ebd src migrations`) was run with this branch's tests and
`-o pythonpath=<base src>`, because `pyproject.toml`'s `pythonpath = ["src"]` otherwise wins:

- all **23** tests in `tests/test_diagnosis_input_provenance.py` fail;
- both new tests in `tests/test_diagnostic_augmentation.py` fail;
- the three re-pointed tests pass, because they cover an invariant that already held.

| Required by the stage | Tests |
|---|---|
| Last verify 1: a snapshot diagnosis carrying a legacy key (held when an opened, searched or unaccountable entry is unsafe; released when it read only safe entries) | `test_a_snapshot_diagnosis_records_the_export_entries_it_opened` (5 cases), `test_the_export_s_entries_map_to_what_they_serve`, `test_the_transport_reports_every_tool_item_it_cannot_read` |
| Last verify 2: a generated topic id in a misconception (held when the drafter read unsafe input; released with a safe, folded record) | `test_a_generated_topic_named_in_a_misconception_carries_what_it_was_drafted_from[tainted, safe]` |
| Last verify 3: a missing C4 receipt (no receipt and no record: incomplete; a receipt naming an unpinned answer: held; recorded in the grading transaction: released) | `test_a_joint_grading_s_inputs_reach_what_is_written_from_it` (3 cases), `test_a_receipt_that_cannot_be_written_commits_no_augmented_grade`, `test_a_committed_joint_grade_carries_its_receipt_and_grading_record` |
| Old rows without records stay held back; a re-diagnosis writes recorded ones | `test_old_rows_stay_held_back_and_a_re_diagnosis_writes_recorded_ones`, `test_a_text_rewritten_by_a_writer_that_recorded_nothing_is_held_back` |
| Regrade lineage keeps a belief resolvable (Q9) | `test_a_regrade_keeps_the_ids_a_belief_lists_resolvable` |
| A question with a recorded contract is shown when safe (Q10) | `test_a_question_that_records_its_contract_is_shown_when_safe`, `test_the_tutor_records_the_contract_a_mid_attempt_question_is_about` |
| Protection routed through `learner_protection` | `test_the_reasons_spelled_out_here_are_the_protection_s`, `test_the_solution_rule_is_the_retrieval_policy_s_window`, `test_a_correction_written_from_exam_material_is_held_back` |
| The release path end to end; the kill switch | `test_a_recorded_diagnosis_is_released_once_its_question_cannot_be_answered_cold`, `test_the_kill_switch_puts_back_the_narrow_rule`, `test_the_records_are_append_only_and_classified` |

## Manual run (backup-API copies, fake diagnoser, no network)

The copies are `fixtures-local/dip-manual-2/{linear_algebra,probability}`, made with
`learnloop.db.copies.copy_tree_with_databases` from the worktree's tracked fixtures. These are the same
snapshots C1a's manual run used (migration 155, mvp-0.8, joint grading), and they migrate to 204 on open.

Setup:

- Each copy's `algorithm_version` was set to `mvp-0.25`, because at mvp-0.8 the split diagnoser's job is
  released `split_disabled`. probability also got `[diagnosis] history_mode = "snapshot"`.
- `LEARNLOOP_CONFIG_DIR` pointed at an empty directory, every `*_API_KEY` was blanked, and the routing
  client builders were replaced with a refusal. The diagnoser was `tests.diagnosis_fakes.ReviewFakeClient`.
- The copies hold joint grades, and `enqueue_diagnosis` queues a live diagnosis only over a blind record.
  So the script queued one live re-diagnosis job per chosen attempt directly, with the payload
  `enqueue_diagnosis` writes, over the attempt's joint grade record. It drained the jobs through the real
  runner.
- Chosen attempts: up to 3 wrong answers on items since answered correctly (window closed), 2 on items
  still open, and 1 exam answer.
- Script: `/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/a22010cc-5149-4947-a2b8-247f18b8f1a0/scratchpad/dip_manual2_run/dip_manual2.py`.
  Outputs: `fixtures-local/dip-manual-2/{linear_algebra,probability}.json`.

| Vault | Re-diagnosed | Records written | What chat releases (recorded rule) | Kill switch off (narrow rule) |
|---|---|---|---|---|
| linear_algebra (70 attempts; 1 closed-window wrong answer, 2 open, 1 exam) | 4 completed (fake: 4 diagnosis calls, 2 recurrence-escalation repair calls) | 4 diagnoses and 12 materialized hypotheses, **all incomplete** | **Nothing**, before or after. Before: 2 open hypothesis statements (1 held back until a record exists, 1 withheld as a diagnostic check). After: 2 diagnosis summaries and their hypotheses plus 6 open hypothesis statements are held back until a record exists; 1 hypothesis statement is withheld as exam material, and 1 hypothesis statement and 1 recurrence-group statement as a diagnostic check. The exam answer's trace is withheld whole, so no diagnosis text appears | Identical tallies |
| probability (2 attempts; snapshot mode) | 1 completed (1 diagnosis call; the fake reported `cat INDEX.md`, receipt `served: entries [INDEX.md]`) | 1 diagnosis and 2 hypotheses, **all complete** | **3 texts**: the diagnosis summary, its hypothesis and the open hypothesis statement (the answer was graded with a C4 receipt; its item has since been answered correctly) | All 3 held back |

Why linear_algebra releases nothing: every re-diagnosis read old joint gradings that were graded before
this stage and have no C4 receipt (`01KY64FZ…`, `01KYF81G…`, `01KYH71A…`), and a prior hypothesis with no
record (`01KYHA8H…`). Records are closed, so each of those inputs makes the whole record incomplete. This is
the fail-closed rule working on real history (see open question 1).

`learning_context` took 547 ms before and 402 ms after on linear_algebra, and 84 and 53 ms on probability.
The first call includes warm-up, so these are not a performance claim. **Paid calls: 0; cost: $0.**

## Gate

Run on the tree of `060645417`, with `TMPDIR` set to the worktree's `fixtures-local/tmp`:

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 22 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **11,682 passed**, 0 failed, 0 skipped, in 12 min 24 s (`fixtures-local/dip-fullsuite-2.log`) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **101 passed**, 11,581 deselected (`fixtures-local/dip-durability-2.log`) |
| `db_generate_reference.py`, then `db_validate_reference.py` | regenerated; `errors: []` |
| Head fixture `fixtures/migration_head_204` | schema version 204, `journal_mode=delete`, `integrity_check` ok, `foreign_key_check` empty |
| Frontend (npm) and `cargo check` | not applicable: nothing under `apps/` changed |
| RPC pins (`tests/test_mobile_allowlist.py`), CLI help | unchanged (no RPC or CLI change) |

The first run (`fixtures-local/dip-fullsuite-1.log`, on `1e36c399c`) had 6 failed and 11,675 passed. They are
fixed above.

## Decisions taken (defaults; the owner may override)

- **An old joint model grade without a C4 receipt is incomplete.** Nothing affirmatively records what that
  grader was shown: the prompt version does not mark C4, and the context hash cannot be reversed. A blind
  grade, a model-free grade and a joint grade with a receipt are accounted for by their own ledgers.
- **A history attempt shown with a grader's output** (failed criteria, fatal errors, first-divergence quotes)
  counts its item's rubric and reference solution as read. The text is then held until that item's attempt
  window closes, using the same threshold the retrieval policy uses to unlock an item's own solution; a test
  pins that the two agree.
- **The snapshot workspace.** An unaccountable report counts as the whole export. No report at all, or a
  path outside the export, makes the record incomplete.
- **A tutor question's reading is recorded incomplete.** The tutor's own inputs (thread, expected answer,
  feedback, passages) are not recorded yet.
- **The kill switch defaults on.**

## Open questions

1. **Existing vaults release almost nothing, even after re-diagnosis.** Diagnosis contexts show old joint
   gradings with no C4 receipt and old unrecorded hypotheses. Records are closed, so one such input holds
   back every text written from it. There are three options:
   - **(a) accept it.** Prose appears as blind-graded history accumulates and old rows leave the neighbourhood.
   - **(b) add an explicit backfill.** A regrade records its grading, and a re-diagnosis records new
     hypothesis versions.
   - **(c) an owner rule.** Joint grades made before C4 shipped (migration 144) would count as "not
     augmented". That is a reading of the migration ledger, not a record, so it was not done without a
     decision.

   Default: (a).
2. **Record the tutor's inputs**, so gap words and beliefs drawn from a tutor question's reading can be
   released. This is a follow-up writer.
3. **The Codex SDK's turn item types** could not be inspected here (the SDK is not installed in this
   environment). The extractor now fails closed on unknown items. One minimal live probe would confirm the
   type names, so a plain read is never over-counted as reading the whole export.
