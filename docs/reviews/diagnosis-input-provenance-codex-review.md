# Diagnosis input provenance: Codex review and fixes

**Status:** all five findings reproduced. F1 to F4 are fixed. F5 is fixed in part (the replay boundary, switch-off
parity with C1a's code, shadow rebuilds and replay tests) and rejected in part (the algorithm successor), under the
owner's standing ruling.
**Review:** Codex job `20261015-110722-OSobP4`, of `499bd3ebd..34d6b8abe` (branch `diagnosis/input-provenance`).
**Fix commit:** `4d83dc264`. **Stage record:** [diagnosis-input-provenance.md](diagnosis-input-provenance.md),
annotated in italics where the review showed a claim did not hold. **Spec:**
[spec_mcp_frontend_c1.md](../specs/spec_mcp_frontend_c1.md) §4.8, updated.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Background shell commands bypass snapshot provenance | **fixed** | `4d83dc264` | `test_f1_shell_control_syntax_is_unaccountable` (27 reports: background `&` bare and in `bash -lc` / `sh -c` wrappers, substitution, expansion, escapes, line breaks, an unterminated quote, a subshell, `env` / `nohup` / `timeout` / `command` / `exec` / `xargs`, `wc --files0-from`, `less -o`, `more +/…`, a two-command `sed` script); `test_f1_a_plain_read_is_still_accounted_for`; end to end, `test_a_snapshot_diagnosis_records_the_export_entries_it_opened[backgrounded_a_read, wrapped_a_backgrounded_read]` (the planted legacy key stays held back, receipt `served.how = whole`) |
| F2 | High | Folding a generated topic ignores whether its provenance covers the title read | **fixed** | `4d83dc264` | `test_f2_a_diagnosis_folds_a_generated_topic_only_under_the_name_it_was_shown[inline, snapshot_graph] × [rewritten, kept]` (the real job: renamed by an unrecorded writer, the summary is held back; kept, it is released as before); `test_f2_the_drafter_folds_a_generated_topic_only_under_the_name_it_was_shown[rewritten, kept]` |
| F3 | High | Concurrent regrades can certify inputs the diagnosis never read | **fixed** | `4d83dc264` | `test_f3_a_regrade_while_the_diagnoser_runs_never_certifies_what_it_was_shown` (the regrade runs inside the fake diagnoser's call; the record stays incomplete with the peer unpinned, the summary held back); `test_f3_a_grading_replaced_after_the_history_was_read_is_unaccountable[regraded, unchanged]` (the window before the freeze) |
| F4 | Medium | Regrading to zero errors loses event lineage | **fixed** | `4d83dc264` | `test_f4_a_regrade_to_no_errors_keeps_the_retired_events_answer` (a real regrade whose grader finds no error: each retired id is recorded with no replacement, resolves to `()`, and the belief keeps its source attempt); `test_f4_retirements_are_idempotent_and_only_for_events_that_left` |
| F5 | Medium | Serving behavior changes without an algorithm successor | **fixed in part** (replay boundary, parity, shadow rebuilds, tests); **rejected in part** (successor) | `4d83dc264` | `test_f5_every_defaults_snapshot_records_the_switch_on`, `test_f5_the_switch_off_is_the_narrow_rule_exactly`, `test_f5_replay_never_reads_the_switch_or_the_records`; switch-off parity with `499bd3ebd` and shadow rebuilds on backup copies (below). Successor: the owner's standing ruling (live changes behind kill switches, not successors, for serving changes replay never reads) |

## What changed

**F1: one strictly validated simple command.** `_SHELL_OPERATORS` listed `&&` but not a single `&`, so
`ls & cat attempts/<legacy>.md` was classified by its first word (`ls`, names only). The shell-operator list is gone.
`provenance.simple_command` accepts a report only when every character is printable, quotes close, and no shell
syntax stands outside single quotes: no `&`, `|`, `;`, `<`, `>`, `(`, `)`, backtick, `$` or backslash (and no `$`,
backtick or backslash inside double quotes). A `sed` print script keeps its literal `$` (`sed -n '$p'`). A reader's
options must match its output-only list (`_READ_OPTIONS`); `wc --files0-from`, `less -o`, `tail -f` and anything
unlisted count as the whole export. A program named by a relative path counts as the whole export. `bash -lc '…'` is
still unwrapped, and its inner command is held to the same rule. An absolute program path (`/bin/bash`) was already
reported as "outside the export", which keeps the record incomplete; that is unchanged.

**F2: a topic's record is folded only under the name the writer was shown.**
`write_provenance.fold_topic_records(…, titles=)` takes each name the writer was shown for a topic. A generated
topic's record covers one text, the name it was written for (the latest row's hash). A topic shown under any other
name folds in as incomplete (`NAME_UNCOVERED`), which holds back everything written from it. The writers capture what
they showed:

- the inline context: the neighbourhood block's titles (`provenance.shown_titles`);
- the snapshot export: each attempt file's topic title, and every title in `graph/learning_objects.md`;
- the prerequisite drafter: each subject concept title, the asking topic's title, and the named prerequisite (the
  reading's first ref, by the reading's name for it).

A topic read by id only (a grading's topic, a closure's topics) folds as before, because its id was minted from the
drafted name its record covers. Direct rendering (`TextGuard._name`) was already right and is unchanged.

**F3: the record is frozen when the context is built.** `run_diagnosis` closes the record right after the context
is assembled, before the diagnoser's call (`provenance.frozen_record`). In the snapshot mode, each export file's
record is frozen when the export is written (`provenance.freeze_entries`; `snapshot_record` joins the ones served).
`jobs._persist` writes exactly that record, carried as `DiagnosisOutcome.record`. A regrade while the model runs no
longer changes contracts, gradings or folded records.

That leaves the window between the history store's read and the freeze. It is closed by marks: the store records
each attempt's grading as it read it (`VaultHistoryStore.grading_marks`, from the same evidence and error-event rows
it shows). The freeze recomputes the marks after building the record and names every attempt whose grading changed
(`GRADING_REPLACED`). A store that cannot say what it showed freezes nothing and records `NOT_FROZEN` (incomplete).
`record_diagnosis_reads(reads=…)` still closes a context built just now; the job never takes that path. The
prerequisite drafter's record is now built before its call, for the same reason.

**F4: retirement without replacement.** Migration 204 is this stage's own and has not landed, so it changed in place:
`error_event_lineage.error_event_id` is nullable. A NULL means the regrade minted no replacement ("no current
error"). A partial unique index, `idx_error_event_lineage_retired`, makes a retirement idempotent.
`record_error_event_lineage` records every retired id (one of the attempt's events before the regrade that is gone
after it). Each retired id is replaced by the events the regrade minted, or by NULL when it minted none.
`replaced_error_event_attempts` keeps the old-event-to-attempt mapping either way, `retired_error_event_ids` names the
no-current-error case, and `current_error_event_ids` resolves a retired id to `()`. The head fixture
`fixtures/migration_head_204` was regenerated from `499bd3ebd`'s 203 head. Its dump differs from the previous one only
in this table's DDL, the new index and the 204 ledger timestamp. It has `journal_mode=delete`, `integrity_check` ok and
an empty `foreign_key_check`.

**F5: the replay boundary, and the successor.**

- **Replay.** `materialize_causal_episode` built each hypothesis's record before
  `append_causal_hypothesis` checked for an identical head. So replay read `text_write_provenance` on every
  re-materialized episode; it wrote nothing. The record is now passed as a function and built only when a new version
  is appended. An idempotent rebuild neither reads nor writes a record:
  `test_f5_replay_never_reads_the_switch_or_the_records` makes every read and write of a record raise during the
  rebuild. A regrade's replay that appends a changed version records it, as any writer does.
- **Kill-switch parity.** `test_f5_the_switch_off_is_the_narrow_rule_exactly`: off, the payload equals reading with
  no record at all (C1a's only source). Against C1a's own code on backup copies holding this stage's records, the
  payloads are byte-identical (below).
- **The successor (rejected).** Handoff §0 rule 5 makes "a change to what is served" a successor with a kill switch.
  The owner's standing ruling, applied at UX Phase 1's landing and cited by facet locks F6, exam protection F6 and plan
  determinism F2, is: live changes behind kill switches, not successors, for serving changes that replay never reads.
  This change fits that ruling:
  - it changes only what the chat read model shows;
  - spec §1 puts no serving, grading or scheduling in C1;
  - replay and rebuild never read the switch, and the shadow rebuilds below are identical with it on and off and
    identical to C1a's code;
  - the switch restores C1a's narrow rule byte for byte.

  The defaults snapshots move only because the effective config gains the switch, as with plan determinism's switch.
  `test_f5_every_defaults_snapshot_records_the_switch_on` pins all seventeen. The owner may still ask for a tag at the
  checkpoint (open question 5).

## Claims that did not hold, corrected

| Claim (stage record) | Correction |
|---|---|
| "Every writer records exactly what it read" | F1 to F3 fixed: a background command is the whole export; a topic folds only under the name shown; the record is frozen when the context is built |
| "A rewritten text without matching provenance stays held back" | It now also holds through folding (F2) |
| "Q9 keeps a belief's replaced event resolvable" | It now also holds when the regrade finds no error (F4) |
| "Replay never reads the new records" | False as built. It now holds for an idempotent rebuild; a replay that appends a changed hypothesis version records it (F5) |
| "No successor is needed because this is only a read-model change" | Restated: the successor is rejected under the owner's standing ruling, with the validation that ruling requires (F5) |

## Spec conformance after the fixes

| Requirement | Assessment |
|---|---|
| Complete diagnosis and snapshot input provenance | F1 to F3 fixed |
| Closed provenance through copy writers | Topic folding checks the shown name (F2); copy writers that read by id fold as before |
| C4 receipt inside the grading transaction (Q14) | Unchanged |
| Regrade event lineage (Q9) | The zero-replacement case is recorded (F4) |
| Question contract recording (Q10) | Unchanged |
| Rubric and reference-solution exposure, shared protection | Unchanged; still routed through `learner_protection` |
| Migration and table ownership | Two append-only `RAW_LEDGER` tables; `error_event_lineage.error_event_id` nullable, plus one partial unique index; no `DERIVED` table |
| Algorithm successor and kill switch | The kill switch's parity and the replay boundary are verified; the successor is rejected under the standing ruling |
| Replay, model, evidence and spend boundaries | No new model call. Replay reads no record on an idempotent rebuild. Nothing is evidence. No paid call |

## Fail first

The pre-review tree was extracted with `git archive 34d6b8abe src migrations` into
`fixtures-local/review-base` and run with this branch's tests and `-o pythonpath=fixtures-local/review-base/src`.
**20 of the 44 new or extended cases fail there**:

- F1: 9 reports (both background forms, `cd … & cat`, `bash -lc` and `sh -c` with `&`, `$PWD`, a backslash, a
  carriage return, `wc --files0-from`), plus both end-to-end background cases;
- F2: all three "rewritten" cases;
- F3: all three cases (the two window cases through the freeze function they call, which did not exist);
- F4: both tests;
- F5: the replay test.

The other 24 are the controls ("kept", the plain reads, `unchanged` aside), the reports the old list already caught
(pipes, `$(`, backticks, newlines and wrappers), the defaults-snapshot pin and the switch-off parity. These cover
invariants that already held.

## Manual run (backup-API copies, fake diagnoser, no network)

Fresh copies `fixtures-local/dip-review/{linear_algebra,probability}` were made with
`learnloop.db.copies.copy_tree_with_databases` from the worktree's tracked fixtures. The setup is the stage's:
`algorithm_version = "mvp-0.25"`, probability in the snapshot mode, an empty `LEARNLOOP_CONFIG_DIR`, every `*_API_KEY`
blank, the routing client builders replaced by a refusal, and `tests.diagnosis_fakes.ReviewFakeClient` as the
diagnoser. Scripts are in `/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/a22010cc-5149-4947-a2b8-247f18b8f1a0/scratchpad/dip_review/`
(`dip_review_run.py`, `parity_dump.py`); outputs are in `fixtures-local/dip-review/`.

- **Re-diagnosis.** The tallies match the stage's run exactly:
  - linear_algebra: 4 diagnoses and 12 hypotheses recorded, all incomplete (the old joint gradings with no C4
    receipt, and one unrecorded prior hypothesis); chat releases nothing, with the switch on or off.
  - probability: snapshot `served: entries [INDEX.md]`; 1 diagnosis and 2 hypotheses, all complete; 3 texts
    released, all held back with the switch off.
- **Switch-off parity with C1a's code.** On each copy, holding this stage's records, `learning_context` was read
  with the same `now` and alias key in three ways: this branch with the switch on, this branch with it off, and
  `499bd3ebd` (the C1a landing, `fixtures-local/base-499bd3ebd/src`).
  - **Switch off and `499bd3ebd` are byte-identical on both copies** (linear_algebra 48,020 bytes, probability
    5,679 bytes).
  - With the switch on, linear_algebra is also identical (nothing is releasable), and probability differs by its 3
    released texts.
  - The live database hashes were unchanged by the reads.
- **Shadow rebuilds.** `learnloop rebuild --shadow --json` ran four times per copy: twice as configured, and twice
  with `--set diagnosis.chat_shows_recorded_text=false`. All 8 runs exited 0.
  - Per copy, the four reports are identical apart from `applied_overrides` and replay-minted ULIDs.
  - They are also identical to a fifth run under `499bd3ebd`'s code.
  - The reported deltas are the copies' own replay drift (linear_algebra: facet 2, mastery 21, schedule 48;
    probability: facet 2, mastery 18, schedule 1). They are the same in every run, so the switch and this stage do
    not cause them.
  - Live DB hashes were unchanged (linear_algebra `ef6422a939e40ac6`, probability `f622be66269835e8`).
- **Tracked fixtures.** The worktree's tracked vaults were opened only by `copy_tree_with_databases`; `git status`
  shows them clean. The owner's checkout was never touched.

**Paid calls: 0. Cost: $0.**

## Gate

Run on the tree of `4d83dc264`, with `TMPDIR` set to the worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 22 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **11,726 passed**, 0 failed, 0 skipped, 20 warnings, in 13 min 50 s (queued 11:54:39, lock 12:04:53, done 12:18:45; `fixtures-local/dip-review-fullsuite.log`) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **101 passed**, 11,625 deselected, in 108 s (queued 12:18:55, lock 12:20:39, done 12:22:29; `fixtures-local/dip-review-durability.log`) |
| `db_generate_reference.py`, then `db_validate_reference.py` | regenerated for the nullable column and the new index; `errors: []` |
| Head fixture `fixtures/migration_head_204` | regenerated: schema version 204, `journal_mode=delete`, `integrity_check` ok, `foreign_key_check` empty |
| Defaults snapshots, CLI help, RPC pins (`tests/test_mobile_allowlist.py`) | unchanged (no config, CLI or RPC change) |
| Frontend (npm) and `cargo check` | not applicable: nothing under `apps/` changed |
| `git diff --check` | clean |

## Decisions taken (defaults; the owner may override)

- **Fail closed on names no record covers.** A generated topic shown under a name its record does not cover makes
  the reader's record incomplete. The drafter is shown concept titles, and a drafted concept's title is not recorded
  (only the topic's title is). So a draft in a subject that already holds a recorded generated topic whose concept
  title differs from its title is held back in chat (open question 4).
- **Topics read by id fold as before.** A generated topic's id was minted from the drafted name its record covers.
  The chat guard still holds the id back when the current title no longer matches (unchanged).
- **The successor stays rejected** under the standing ruling, with the parity and rebuild validation above.
- **Migration 204 changed in place.** It has not landed; the head fixture and the reference were regenerated.

## Open questions

The stage record's questions 1 to 3 stand. Added:

4. **Record a drafted concept's title.** Today only a generated topic's title is covered, so a drafter shown another
   drafted concept's title cannot fold that topic's record. Recommended default: in a follow-up, have the
   prerequisite writer also record the drafted concept title as a covered name of the topic. Until then, the
   affected drafts are held back in chat.
5. **The successor.** It was rejected under the standing ruling. If the owner wants a tag at the checkpoint, it would
   be the next free tag after main's at landing, with `diagnosis.chat_shows_recorded_text` as its kill switch.
