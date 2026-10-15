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
**Landed** on main 2026-10-15 as migration **205**, with the chat release switch
(`diagnosis.chat_shows_recorded_text`) **off**: the final verify reopened F2 and F3 in the release path. See
[Landing onto main](#landing-onto-main).

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
| Diagnoser | `diagnosis` | Every attempt its context showed (with the grading folded in, and the item's solution counted as read, when a grader's output about it was shown), the diagnosed item's rubric and reference solution, the neighbourhood's topics, every prior hypothesis, registry statement, repair and unresolved-cause factor read (their records folded in, each checked against the text it showed). *Codex review F3: the record was closed at persistence, after the model ran, so a regrade meanwhile could certify a grading the diagnoser never saw. It is now frozen when the context is built (`provenance.frozen_record`), with each grading's mark checked against what the history store read. F2: a generated topic's record is folded only when it covers the title the context showed. Re-review F3: the marks were read lazily with the history's rows, not with the blind payloads captured earlier, and the diagnosed attempt's grade was read on its own; a grading's identity (payload, contract, provenance) is now read in one snapshot with the overlay, the diagnosed attempt's grade comes from that overlay, and the freeze reads the record and the identity in one snapshot. Re-review F2: a name shown is checked even when the topic's record was already folded in* | `diagnosis/split/provenance.py`, `context.py`, `diagnoser.py`, `jobs.py` (`_persist` → `record_diagnosis_reads`, in the diagnosis's transaction, the record frozen before the model call) |
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

## Landing onto main

**Branch:** `merge/provenance-onto-main` (worktree `learnanything-merge2`), from main `37a2a7e5f` (`mvp-0.25` LATEST; migration head 204, re-read safety's `source_held_out_signal_marks`; head fixture `fixtures/migration_head_204`; seventeen defaults snapshots `mvp-0.9`..`mvp-0.25`). Not pushed. Owner-directed, 2026-10-15, single phase. The sections above and the Codex review record describe the branch as built (tip `17d386fdb`), and keep its placeholder migration number (204) and its switch default (on).

**Commits:**
- `cbbeee14a`: a real `--no-ff` merge of `diagnosis/input-provenance` (`17d386fdb`, unchanged, 7 commits from `499bd3ebd`), with the conflict resolution and the renumber. The release switch is still the branch's in this commit (on).
- `7fdce04f0`: the release switch off, the seventeen snapshots, and the landing and composition tests.
- `55d5383b7`: the regenerated references and the Pipeline Map.
- This record.

**Main since `499bd3ebd`, composed:** re-read safety and exam protection by extraction identity (migration 204, rule 4, identity-bound marks, the one alias authority, coordinated migrations with F8's run-time allowances), the Marker pdfium worker, GLM-OCR quality, and the adaptive-difficulty spec revision. No algorithm successor: the landing changes no scoring, scheduling or projection, and with the switch off no serving.

### The release switch is off, and why

The final Codex verify of the branch (job `20261015-132314-nwmTQW`) confirmed F1 fixed and **reopened two High findings in the release path**:

- **F2.** The stuck-answer gap reader's `reading_record` (`diagnosis/text_gaps/provenance.py`, called by the belief writer in `text_gaps/actions.py`) calls `fold_topic_records` without `titles`. A generated topic renamed by a writer that records nothing, shown to the gap reader under its new name (`sources.stuck_answer_text` puts the title in the context), folds its old record as complete. `TextGuard` withholds the title itself but releases a belief statement that repeats it.
- **F3.** C4 history dependencies escape grading validation. A legacy joint grading A with no stored grading record but a C4 receipt naming history attempt B is folded through `grading_record(A)` after `frozen_record` / `freeze_entries` chose the attempts to check (only those listed directly, and factor attempts). B regraded between the history read and the freeze leaves A's record complete, naming B's new contract.

The owner's ruling is "land narrow, then fix source". The recording infrastructure lands; the release does not:

- `diagnosis.chat_shows_recorded_text` defaults **false** (`config/schema.py`). The decision-only template leaves the key out, as on the branch. `default_provenance` reads a missing or unreadable switch as off.
- With it off, chat's `learning_context` (and `today` and `progress`, through the same `TextGuard`) read with `no_write_provenance`: every model-written text is held back with C1a's reason, exactly as main's narrow C1a. The `learning_context` tool's description is C1a's again ("held back for now").
- **The writers record either way:** gradings, diagnoses (frozen at context build), hypotheses, candidates, misconceptions and corrections, gap words, drafted topics and seeded items, Q9's lineage and Q10's question contracts. So the follow-up starts from recorded history.
- **The follow-up, "one context capture point":** route every model-context build (the diagnoser's inline and snapshot contexts, the gap reader, the prerequisite drafter, the joint grader's C4 history, the tutor) through one capture point. It records what the model was shown where the context is built (every name with the text shown, every dynamically resolved answer or contract dependency, C4 history included) and validates it as one identity at the freeze. Then it needs a clean verify. Only then is the switch turned on.

### Conflicts

377 files:
- **375 generated reference notes**: main's side, then regenerated.
- **The head fixture's `README.md` and `state.sqlite`**: both sides had built a `migration_head_204` (main's re-read safety, the branch's provenance). Main's side was taken, then renamed and rebuilt (below).

Every other file merged cleanly. The 24 test files, both reference scripts and `docs/decider-tier1-migration.md` had moved the head path from 203 to 204 identically on both sides. Shared source files (`config/schema.py`, `db/repositories.py`, `db/table_roles.py`, `tutor/tutor_qa.py`, `tests/test_architecture.py`) merged without overlap and were read after the merge.

### The renumber: migration 204 → 205

- **Migration.** `migrations/204_write_provenance.sql` became `migrations/205_write_provenance.sql`. Its header names both numbers (built as 204, a placeholder, renumbered 205 after re-read safety's 204). Only a comment changed.
- **Table roles.** `text_write_provenance` and `error_event_lineage` stay `RAW_LEDGER` in `table_roles.py` (comments say migration 205), so they need no replayer. The `question_events` column needs none.
- **Every mention of the provenance migration says 205:** `db/stores/write_provenance.py`, `learner_context.py`, `table_roles.py`, `tests/test_diagnosis_input_provenance.py` (including the migration file path its F4 test reads), `tests/test_architecture.py` and spec §4.7/§4.8. The held-out signal ledger's mentions of 204 are re-read safety's and stay.
- **Head fixture.** `git mv fixtures/migration_head_204 fixtures/migration_head_205`. Its `state.sqlite` was rebuilt:
  - a backup-API copy (`learnloop.db.copies.backup_database`) of main's 204 database (blob `85d9de239`);
  - only 205 applied, through `apply_migrations` under the test suite's allowance (`upgrade_allowance(UPGRADE_TEST_HELPER)`: F8 refuses an upgrade outside one);
  - `wal_checkpoint(TRUNCATE)` → `(0, 0, 0)`, then `journal_mode=DELETE` (header bytes 18-19 are 1/1);
  - `integrity_check` ok, `foreign_key_check` empty;
  - copied back with the backup API, with no companion files.

  Its `sqlite_master` equals the branch's head-204 fixture's plus main's `source_held_out_signal_marks` (table, two indexes, its autoindex and trigger). The new tables have 0 rows. The README gains the 205 paragraph and the build chain.
- **Hard-coded head paths.** 24 test files name `migration_head_205`. So do both reference scripts (`SCHEMA_PATH`, `SCHEMA_HEAD = 205`, the generator's other mention) and `docs/decider-tier1-migration.md`. The max-migration assertion in `test_route_rules_in_grader.py` is 205.

### Coordinated migrations

The branch adds no `Repository(path)` construction or `apply_migrations` call in `src/` or `scripts/`. Its new tests' `Repository(paths.sqlite_path)` (`tests/test_diagnostic_augmentation.py`) attaches a freshly created, current database, which needs no allowance. `tests/test_coordinated_migrations.py` needed one change. `test_f8_the_coordinator_upgrades_under_its_allowance_and_qualifies` upgrades an older build that lacks the ledger's migration (204), but asserted that the coordinator applied the *newest* migration. With 205 on top, that is 204, so the test now looks up the ledger's migration by name. All 20 cases pass, under the test pragmas and under `--durable-sqlite`.

### The switch off: what changed

- `config/schema.py`: `chat_shows_recorded_text: bool = False`, with a comment giving the reason and the follow-up.
- `learner_context.py`: `default_provenance` defaults to off; the module doc says rule (c) is behind the switch, off by default, and that off is C1a's narrow rule exactly.
- `learnloop_mcp/server.py`: the `learning_context` tool's description is C1a's again; the schema comment names the switch. `remote/views.py`'s doc names it too.
- Spec `spec_mcp_frontend_c1.md`: §4.7 rule (c) says off as landed, and §4.8 ends with the landing paragraph (F2, F3, the follow-up).
- **Defaults snapshots.** All seventeen `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries were recomputed with `defaults_fingerprint_for_version`, after deleting `config/__pycache__/template.cpython-312.pyc` and touching `template.py`. Every one moves, because the effective config now carries the key as `false` (main has no key; the branch had `true`); no other leaf moves. The template comment records the switch, its default off at landing, and why.
- `tests/test_diagnosis_input_provenance.py` keeps covering the release path as an owner who turns the switch on has it. Its `_context` reads through `_switched_on`, which turns the switch on unless the vault's `learnloop.toml` sets it. So the kill-switch tests that write `false` keep their meaning. `test_f5_every_defaults_snapshot_records_the_switch_off` pins all seventeen snapshots with the switch off. The replay test rebuilds once with the switch on, then once with it off.

### Landing and composition tests

`tests/test_diagnosis_input_provenance_landing.py`, 11 cases (9 pass, and 2 are strict xfails):

| Test | What it shows |
|---|---|
| `test_the_release_switch_defaults_off_and_the_default_source_is_the_narrow_rule` | The schema and a new vault have the switch off; `default_provenance` is `no_write_provenance` (an unreadable config too); `true` in `learnloop.toml` selects the recorded source |
| `test_off_a_fully_recorded_safe_text_is_withheld_in_chat_and_the_writers_still_record` | A diagnosis summary and a belief with complete records and safe inputs (window closed). Through the MCP server's `learning_context` tool (fresh attach), both are held back with C1a's reason, nothing of either is in the payload, and the tool's description is C1a's. `learning_context` equals the `no_write_provenance` payload byte for byte. Switched on, both are shown, as `RecordedText` |
| `test_off_the_live_pipeline_records_and_chat_withholds_until_the_switch_is_on` | The real door (blind grader, diagnoser job, materialized hypothesis) with the switch off: the grading, diagnosis and hypothesis rows are written and complete; after the correct answer, chat still holds the summary and cause back. On, both are shown |
| `test_off_f2_a_belief_from_a_renamed_generated_topic_is_withheld` | F2's reproduction (a drafted topic renamed by an unrecorded writer, a stuck answer read with the new title, `record_belief`'s write): the candidate's record says complete (the defect), and with the switch off the statement is held back |
| `test_on_f2_…` (strict xfail) | The same with the switch on asserts "withheld"; today the statement is released, so it xfails. The follow-up turns it into a pass (and `strict` fails the suite until the mark is removed) |
| `test_off_f3_a_summary_over_a_regraded_c4_history_attempt_is_withheld` | F3's reproduction (legacy joint grading `PEER` with a C4 receipt naming `att_b`; the store's marks captured while `att_b` pins `acv_own`; `att_b` re-pinned to `acv_own_v2` with its grading record; `frozen_record`, persisted as `jobs._persist` does): the record is complete and names `acv_own_v2` (the defect), and with the switch off the summary is held back |
| `test_on_f3_…` (strict xfail) | As for F2 |
| `test_the_reproductions_hold_no_name_or_key_with_the_switch_off` | Both reproductions together through the MCP tool: neither the renamed title nor the summary reaches the payload |
| `test_rule_4_and_identity_bound_marks_reach_rule_c_through_learner_protection` | Composition 1, below |
| `test_a_method_explicit_question_records_the_contract_it_was_presented_with` | Composition 2, below |
| `test_q14_on_a_vault_the_coordinator_upgrades_the_receipt_commits_with_the_grade` | Composition 4, below |

Both xfails were checked with `--runxfail`: each fails on its own assertion (F2: "Thinks Parity, renamed by a writer that recorded nothing needs no sign rule" released; F3: the summary released). No other error.

### Compositions

1. **Rule 4 and identity-bound marks reach rule (c) through `learner_protection`.** Rule (c)'s input check reads items through `learner_protection.withheld_items` (which routes exam decisions through `exam_material`) and source refs through `exam_material.source_ref_protected` (`PastWork.source_reason`). Re-read safety's rule 4 puts an unmarked reading of a protected book into that material whole, so no code change was needed. In re-read safety's own landing world (`reread_world`, the book read again as `ext_book_r2`, an item made from the re-read's own passage):
   - a diagnosis that read the answer on that item, and a correction written from that passage, are recorded complete;
   - switch off, both are held back with C1a's reason; switch on, both are shown while the book is unprotected;
   - then the owner marks a section of the book's **first** reading (an exact mark bound to `ext_book`'s identity). The re-read is held back (`reading_held_back`), the item is `exam or held-out material`, and both texts are withheld with that reason.
2. **Method-explicit's `answered_prompt` for pinned questions.**
   - `pi_own` is given a required method. The tutor's Q10 writer (`_question_contract`, mid-attempt) records `snapshot_for_presentation`'s contract. That contract freezes the method, and `answered_prompt(item, contract)` equals `presented_prompt(item.prompt, item.required_method)`, the question the learner was shown, ending with the method's sentence.
   - An answer graded under that contract shows that question in chat (rule (a)), identically with the switch off and on.
   - A question recorded with the contract is held back off, and its words are shown on.
3. **The Marker and GLM workers are unaffected.** The branch changes nothing under `ingest/`, `content/sources/` or `content/pipeline/`, and no worker reads a provenance table or the switch. Their tests (`test_marker_pdfium_worker.py`, `test_glm_ocr.py`, `test_reread_safety*.py`) pass in the full suite unchanged.
4. **The C4 receipt inside the grading transaction composes with the coordinated grading paths.** Main's grading code is unchanged since `499bd3ebd` (`attempts/` untouched there), so Q14 merged as built. The composition is the database it runs on:
   - a vault an older build wrote (205 rolled back: both tables, the column and the ledger row) is refused by a bare `Repository(path)` (`UncoordinatedMigrationError`);
   - it is opened through the coordinator (`vault_repository`, which upgrades it to 205 under the vault lock);
   - a joint grade on it commits with exactly one Phase-C receipt and one complete grading record;
   - with the receipt write failing, the model grade rolls back and the door's self-grade commits, with no model evidence, no receipt and no grading record.

   This passes under `--durable-sqlite` too.

**Also:**
- The CLI help snapshot was regenerated (`python tests/test_cli_help_snapshot.py --write`) and did not change.
- The RPC pins (`tests/test_mobile_allowlist.py`, `test_desktop_rpc_contract.py`, the sidecar serializer snapshot) pass unchanged: no RPC changed.
- Nothing under `apps/` changed, so neither the frontend nor `cargo check` applies.

### Generated files

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**; schema head 205, 324 table notes (two new: `text_write_provenance`, `error_event_lineage`, `RAW_LEDGER`), 858 effective configuration leaves (`diagnosis.chat_shows_recorded_text`, `false`). `Database.md`'s prose counts were corrected by hand: 324 tables, 19 `DERIVED`, 305 others, 858 leaves.
- `validate_vault.py` passes: 1,109 notes, all 1,107 non-template notes reachable from Home.
- **Pipeline Map.** A "Write-time provenance (migration 205; chat release off)" entry under grading and diagnosis covers:
  - the writers and what they record;
  - Q14, Q9 and Q10;
  - rule (c) behind the switch, off, with the two reopened findings and the follow-up;
  - that nothing is evidence and replay never reads the records.

  The diagram gains the ledger, the chat frontend entry says the release is off, the replay entry names both tables as raw, and the source paths and gaps list follow.

### Gate

Run on the final code tree, `55d5383b7`; only this record was committed after it. `TMPDIR` was the worktree's `fixtures-local/tmp`. No paid calls ($0.00): every test uses fakes.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` (5.14.0); `uv run --no-sync` afterwards | ok |
| `uv run --no-sync lint-imports --no-cache` | **22 kept**, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto -q -p no:cacheprovider` | **11,921 passed, 2 xfailed** (the strict F2/F3 marks), 0 failed, in 18 min 19 s (lock 14:15:38, done 14:33; `fixtures-local/prov-fullsuite.log`) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability -n auto` | **106 passed** in 26 s (`fixtures-local/prov-durability.log`) |
| `db_generate_reference.py` / `db_validate_reference.py` / `validate_vault.py` | regenerated / 0 errors / passes (above) |
| Head fixture `fixtures/migration_head_205` | schema version 205, `journal_mode=delete`, `integrity_check` ok, `foreign_key_check` empty, no companion files |
| CLI help snapshot (`--write`), RPC pins | unchanged |
| Frontend (npm) and `cargo check` | not applicable: nothing under `apps/` changed |
| `git diff --check` | clean |

Nothing failed, so nothing needed a rerun alone.

**Tests:**
- 11 added in `tests/test_diagnosis_input_provenance_landing.py` (9 pass, 2 strict xfails);
- `tests/test_diagnosis_input_provenance.py` reads with the switch on (`_switched_on`) and pins the snapshots off;
- `tests/test_coordinated_migrations.py`'s coordinator test looks up the ledger migration by name;
- 24 test files' head path, and `test_route_rules_in_grader.py`'s max migration, moved to 205.

### Parity

**Setup:**
- **Copies.** Backup-API copies (`copy_tree_with_databases`) of this worktree's tracked `fixtures/linear_algebra` and `fixtures/probability`, under `fixtures-local/tmp/prov-parity`, two of each (one per side).
- **Main's side.** Main `37a2a7e5f`, exported with `git archive` (`src`, `migrations`) and put first on `PYTHONPATH`; every run printed the export's `learnloop/__init__.py`. Its coordinator (`open_vault_repository`) applied 49 migrations to each copy, 155 → 204.
- **The merge's side:** 50 migrations, 155 → 205, by the merge's coordinator.
- **Runs.** On each copy, with `LEARNLOOP_CONFIG_DIR` set to an empty directory: `learnloop rebuild --shadow --json`, `learnloop doctor --json`, and chat's read views. The views (`learning_context`, `today`, `progress`) were read through `RemoteRuntime.attach`, the MCP server's read-only attach, with a fixed clock and alias key, and written as sorted JSON.
- **Comparison.** Shadows were compared structurally, with ULIDs, timestamps, hashes and paths set aside. Doctor reports were compared positionally and as multisets, with the copy's directory name normalized. Chat views were compared byte for byte.

| Fixture | Shadow (facet / mastery / schedule) | Shadow differences | Doctor main → merge | Chat views (switch off) |
|---|---|---:|---|---|
| linear algebra | 22 / 6 / 47 on both sides | **0** | 107 → 107 (1 error, 106 warnings); identical positionally and as multisets | **byte-identical** (37,520 bytes) |
| probability | 2 / 1 / 1 on both sides | **0** | 138 → 138 (49 errors, 46 of them `criterion:unknown_dependency`); identical | **byte-identical** (5,985 bytes) |

**Checks:**
- **No doctor additions.** The branch adds no doctor check, and the reports are equal.
- **Q14 only moves a failure path.** A successful grading writes the same rows as before plus one record, and nothing grades during these runs. The rebuild's learner-state diff and its replayers are the same on both sides.
- **The new tables are empty on the merge's copies** (`text_write_provenance` 0, `error_event_lineage` 0, no question with a recorded contract). The upgrade writes nothing, and neither do shadow or doctor. Records start with the first grading after the upgrade.
- **Chat is C1a's.** With the switch off (the merge's copies read `False`; main's config has no key), `learning_context`, `today` and `progress` are byte-identical to main's code on the same data.
- **The copies are unchanged.** `live_database.unchanged` is true on every shadow, and each copy's `state.sqlite` hash (checkpointed) is the same before and after the shadow, doctor and view runs.
- **The tracked fixtures were only copied.** `git status --porcelain fixtures/` is empty before and after. `arxiv_v2` was not opened, and the main checkout and the source branch were not touched.

### Open questions for the owner (defaults as landed)

1. **Old vaults release almost nothing, even with the switch on.** Diagnosis contexts show old joint gradings with no C4 receipt and unrecorded prior hypotheses, and one such input holds back everything written from it (the stage's manual run: linear algebra released nothing). **Default: (a) accept.** Prose appears as blind-graded history accumulates. No backfill (b) and no "pre-C4 joint grades count as not augmented" rule (c) without an owner decision. While the switch is off this changes nothing chat shows.
2. **Tutor inputs are unrecorded.** A tutor question's reading (the tutor's thread, expected answer, feedback and passages) is recorded **incomplete**, so a belief, a drafted topic or a seeded item drawn from it stays held back. **Default:** held back; recording the tutor's inputs is a follow-up writer, naturally part of the one-capture-point follow-up.
3. **The Codex SDK's turn item types are unverified.** The SDK is not installed here, so the snapshot-mode extractor fails closed: an item it cannot read counts as reading the whole export, and no report makes the record incomplete. **Default:** fail closed. One minimal live probe (owner-approved, paid) would confirm the type names so a plain read is not over-counted.
4. **Concept-title coverage.** A generated topic's record covers its topic title, not its drafted concept title. A drafter shown a concept title that differs from the title folds the topic as `NAME_UNCOVERED` (incomplete), and the draft is held back. **Default:** held back. Recommended follow-up: record the drafted concept title as a covered name of the topic.

The successor question (Codex review, open question 5) is moot at this landing: with the switch off nothing served changes, and Q14 only moves a failure path (a receipt that cannot be written now fails the grading, and the door's self-grade commits). If the follow-up turns the switch on, the owner's standing ruling (live changes behind kill switches) applies, or a tag at that checkpoint.
