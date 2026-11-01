# Learner-blindness relax: Codex review (gpt-6.1-sol) and fixes

Stage `learner-blindness-relax`, branch `learner/blindness-relax` (stage commit `2899bfdf43`). Codex job
`20261101-153225-iy7OXO`. Codex's own targeted pytest did not start (its sandbox could not reach the user bus for
`systemd-run --user`), so its three findings were source-traced. Each one was reproduced here with a failing test
against the pre-fix source before it was fixed. All three show a path to exam leakage or to released text that
depends on a solution, which is the bar the owner set for this stage. None of them is a blindness finding outside
grading.

## Review

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Stored tutor answers bypass source-level exam protection | fixed | `adb862f63e` | `tests/test_learner_blindness_relax_codex_review.py::test_a_stored_answer_whose_linked_passage_is_held_out_since_is_withheld`, `::test_a_stored_answer_retrieved_from_a_passage_held_out_since_is_withheld`, `::test_an_answer_whose_passages_cannot_be_established_is_withheld` |
| F2 | High | Unrelated switches disable the new state path's cold protection | fixed | `adb862f63e` | `::test_with_both_rw1c_switches_off_a_bound_session_carries_no_learner_state`, `::test_with_both_rw1c_switches_off_a_cold_bound_session_carries_none_as_cold`, `::test_an_unbound_workbench_session_still_carries_the_learner_state` |
| F3 | Medium | Prior workbench traces are omitted from diagnosis provenance | fixed | `adb862f63e` | `::test_an_earlier_workbench_trace_counts_its_item_and_leaves_the_record_incomplete` |

**Reproduction.** The new test file ran against the stage's pre-fix source: the source files were restored from
`HEAD`, the tests run, and then the fixed files were copied back. Results:

- **F1:** the feedback answer `SECRET_WORKED_SOLUTION 42` was still `answer_shown` after its topic's linked passage
  `ext_book/s2` was marked held out.
- **F2:** with both RW1c switches off and `coldActive` omitted, a question from a session bound to the item put
  `learner_state` into the tutor prompt. The same happened when an open cold retry held that item.
- **F3:** the item of a passing prior attempt whose trace was shown was missing from the record's `solution_items`.

### F1: stored answers are checked by their passages (fixed)

Before this fix, `reader_learner_state` re-showed a practice or feedback answer once its item was unprotected and
its attempt window closed. It never checked the passages that answer was written from. Now an answer shows only when
every passage it may have read passes `PastWork.source_reason`, the shared exam and held-out predicate
(`exam_material.source_ref_protected`). That predicate is conservative where it cannot place a block. The passages
come from the new `reader_learner_state.answer_source_refs`:

- **The item's linked passage pool.** A row records nothing about the passages the tutor's linked delivery used, so
  the whole pool counts. The new helper `content.authoring.practice_leakage.teaching_link_refs` returns the semantic
  links of the item's topic and its facets. It applies no status filter and no exam filter, so a passage that has
  become held out since the answer was written is still in it.
- **The provider's recorded `source_retrieval.span_keys`.** Both the `extraction/span` form and the
  `extraction:span` form are accepted.
- **The references the provider or the delivery followed** (`references.resolved`).
- **The citations the answer kept.**

When the passages cannot be established, the answer is left out with `ANSWER_SOURCES_UNKNOWN`. That covers a
retrieval that says it delivered passages without naming them, and any record that cannot be read. The learner's own
question still shows. The answer is left out with the reason recorded and counted under `answers_left_out`. The rest
of the item's context (prompt, rubric, grading feedback, thread) is item-scoped and already covered by the item's
protection.

**Residual, below the proportionate bar.** Blocks that the delivery's statement completion (`hydrate`) appended to
a linked passage are not checked one by one. Those blocks are the rest of the same numbered environment, and
completion stops at headings. A held-out unit marked since that covers the linked block is caught. One that starts
mid-environment, right after it, is not.

### F2: a bound session with both RW1c switches off carries no learner state (fixed)

With `retrieval_enabled` and `offers_enabled` both off, `restriction()` stays the base Reader's on purpose. It
derives no server-side cold status and builds no binding, so no item guard runs and no accounting is attached. That
byte-for-byte base behaviour is pinned by RW1c's switch-off golden and is not changed here.

`RTU.learner_state` now resolves a named workbench session on the server whenever the restriction is inactive:

- if the session is in a cold administration, the state is omitted as `cold_administration`;
- if the session is bound to an item, the state is omitted as the new `unguarded_workbench_binding`, because nothing
  would guard the call or attach its help to the item;
- if the session cannot be resolved, the state is omitted as `protection_unreadable` (fail closed);
- a session that binds no item still carries the state.

This is stricter than Codex's suggestion. Codex proposed resolving the binding and passing it through, but
accounting and the item guard are built only by RW1c's `bound_ask`. Leaving the state out adds no new text to an
unguarded call, so contaminated work cannot stay labelled cold through this path. With either RW1c switch on, the
existing path holds: server-derived cold returns no state, and a bound question carries no earlier tutor answer
under the binding's guard.

### F3: an earlier workbench trace folds into the diagnosis record (fixed)

In the prior-analysis arm's `on` arm, a shown prior attempt's `workbench_trace` now adds two things to the
diagnosis's `DiagnosisReads`:

- **Its item as a solution read.** The hints, checks and discriminating questions were written with that item's
  rubric, reference solution and approach map.
- **An `unaccounted` reason, which makes the record incomplete** (`prior_analysis.TRACE_UNRECORDED`). The
  `help_assists` rows record no write-time provenance for what their writers read: passages, hypotheses, the
  learner's attempts.

The record from `diagnosis_record` is therefore `complete = False`, and the recorded-text release
(`diagnosis.chat_shows_recorded_text`) never releases that diagnosis, whatever the earlier item's attempt window.
The test pins that the earlier item is in the record's `solution_items` and that the record is incomplete, while
the arm-less context's record stays complete. The `off` arm's reads equal the arm-less context's.

**Out of scope, recorded.** The diagnosed attempt's **own** workbench trace (RW2b) is accounted only by its item
being a solution read. It is not marked incomplete for its assists' passages. That predates this stage and is left
for its own follow-up.

### Claims Codex said don't hold

All three are corrected by the fixes:

- Exam protection now covers archived answers by their passages (F1).
- Cold and bound-workbench protection hold whatever the RW1c switches (F2).
- No assistance enters a bound question's context when no accounting is attached (F2).

Codex's narrower claim holds: the direct blind-grader prompt builders are unchanged, and the joint-grading issue
predates this diff (owner item in `learner-blindness-relax.md`).

## Gate (this fix step; the full suite runs once in the landing gate)

Every pytest run was inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, with TMPDIR
outside the worktree. No live or paid call was made, no owner vault was opened, and only synthetic vaults and fakes
were used.

- `uv sync --extra dev --extra mobile`, plus `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **40 kept, 0 broken**.
- Reproduction (pre-fix source): `uv run pytest -n 6 -q tests/test_learner_blindness_relax_codex_review.py`
  gave 7 failed. Three of those failures were the behavioural reproductions above. Three more were attribute errors
  on names the fix adds. The last was the unbound-session helper's `import_status`, which was then corrected in the
  test.
- Fixed tree: `uv run pytest -n 6 -q tests/test_learner_blindness_relax_codex_review.py` gave **7 passed**.
- Targeted run, `uv run pytest -n 6 -q` on the files below: **1270 passed, 2 xfailed, 0 failed** (193 s).
  - Added or changed: `tests/test_learner_blindness_relax_codex_review.py`
  - Stage tests: `tests/test_learner_blindness_relax.py`
  - Diagnosis context, provenance and arm: `tests/test_diagnosis_context.py`, `tests/test_diagnosis_contract.py`,
    `tests/test_diagnosis_history_modes.py`, `tests/test_diagnostic_augmentation.py`,
    `tests/test_diagnosis_input_provenance.py`, `tests/test_diagnosis_input_provenance_landing.py`,
    `tests/test_mcp_c1a_landing.py`
  - Practice leakage and exam protection: `tests/test_practice_leakage.py`, `tests/test_exam_protection.py`,
    `tests/test_exam_protection_identity.py`, `tests/test_hint_blind.py`, `tests/test_method_explicit_landing.py`,
    `tests/test_pfc_unassessed_readers.py`, `tests/test_ad23_contract.py`
  - Reader tutor and RW1c: `tests/test_reader_rw1c_review.py`, `tests/test_reader_rw2b_fix15.py`,
    `tests/test_reader_tutor_retrieval.py`, `tests/test_reader_tutor_offers.py`,
    `tests/test_reader_tutor_switch_off.py`, `tests/test_reader_find_sources_callers.py`,
    `tests/test_library_ask_review.py`, `tests/test_figures_show_me.py`, `tests/test_reader_ca2_astra_handoff.py`,
    `tests/test_reader_ca2_astra_handoff_recovery.py`, `tests/test_reader_ca2_codex_rereview.py`,
    `tests/test_reader_ca2_codex_review.py`, `tests/test_reader_ca2_one_ask.py`
  - Learner protection readers: `tests/test_deliverable_path.py`, `tests/test_reread_safety_landing.py`,
    `tests/test_router_r2a_landing.py`, `tests/test_router_r2c_teach_back.py`, `tests/test_secondary_attach.py`,
    `tests/test_teacher_te0_confidence_events.py`, `tests/test_teacher_te0_fix_round2.py`,
    `tests/test_teacher_te0_review_fixes.py`
  - Contracts: `tests/test_architecture.py`, `tests/test_desktop_rpc_contract.py`, `tests/test_mobile_allowlist.py`,
    `tests/test_table_roles.py`

These steps did not apply and were not run:

- No config key was added, so the config defaults snapshot was not rerun.
- No CLI surface changed.
- No migration, DB code or connection code changed, so there was no durability run and no DB reference run.
- No frontend or `src-tauri` change, so no npm, vitest or cargo run.
- No new constant was added that needs classification. The new values are reason strings and an omission label,
  not weights or thresholds.

## Re-review (Codex job `20261101-155305-nSMdrA`, verdict REOPENED)

Codex's runner again could not reach the user bus for `systemd-run --user`, so its validation was source-based. It
named no new defects in the fix commits.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | REOPENED: a stored answer's source check omits the earlier tutor turns its thread gave it | fixed | `571559eff2` | `tests/test_learner_blindness_relax_codex_review.py::test_a_later_turn_that_was_given_an_earlier_turn_from_a_passage_held_out_since_is_withheld`, `::test_a_feedback_turn_inherits_the_earlier_feedback_turns_of_its_attempt`, `::test_an_earlier_turn_whose_passages_cannot_be_established_withholds_the_later_answer` |
| F2 | High | Unrelated switches disable the new state path's cold protection | confirmed fixed (no change) | `adb862f63e` | Codex confirmed the server-side session resolution closes the path |
| F3 | Medium | Prior workbench traces are omitted from diagnosis provenance | confirmed fixed (no change) | `adb862f63e` | Codex confirmed the record is incomplete and the diagnosis withheld |

**Reproduction.** The three new tests were run against `9cb9199ce3` (before this fix), and all three failed:

- In Codex's two-turn scenario, Q1 was written from `ext_book/s11` and Q2 from the clean `ext_book/s12`, with Q1 in
  Q2's thread. After `s11` was held out, Q2's answer `Q2_ANSWER_RESTATING_Q1` was still `answer_shown`.
- An earlier feedback turn on the same graded attempt was written from `s11`. After `s11` was held out, the later
  feedback answer on that attempt still showed.
- An earlier turn's retrieval said it delivered passages without naming them. The later answer still showed.

### F1: the answer's check includes every earlier turn of its thread (fixed)

`reader_learner_state._thread_turns` reads every earlier turn the tutor may have been given with a stored answer.
`tutor_qa._thread` gives a practice answer the attempt's earlier answered practice turns on the item, and a feedback
answer the earlier answered feedback turns on its graded attempt. `_thread_turns` reads a superset of each:

- **Practice:** every earlier answered practice turn on the item, whatever its window, session or attempt key.
- **Feedback:** every earlier answered feedback turn on the attempt.

That set is transitively closed. An earlier turn's own thread is earlier still and has the same key, so it is
already in the set. Question rows are never rewritten after they are answered, and each keeps its recorded
`source_context`. The table is therefore the per-answer provenance record. Reading it at check time also covers rows
written before this stage, with no migration. Recording the same thing again at write time would duplicate it.

The answer's passages and those of every turn in its thread are now checked together by `PastWork.source_reason`.
For each turn, these count:

- its own linked pool;
- its retrieval spans;
- the references it followed;
- the citations it kept.

The answer is withheld with `ANSWER_SOURCES_UNKNOWN` when the provenance cannot be established:

- any turn's passages cannot be established;
- a turn's item is no longer in the vault, so its linked pool cannot be read;
- the row has no item or attempt key, so its thread cannot be established.

A turn whose answer was withheld as worked help is skipped. Its thread carried the take step
(`delivered_answer_md`), never the withheld text. A practice turn is not in a feedback answer's thread, so the
seeded feedback answer still shows when only a later practice turn read a held-out passage. That case is pinned.

## Re-review gate (this fix step; the full suite runs once in the landing gate)

Every pytest run was inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, with TMPDIR in
the stage scratch directory outside the worktree. No live or paid call was made, and no owner vault was opened. Only
synthetic vaults and fakes were used.

- `uv sync --extra dev --extra mobile`, plus `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **40 kept, 0 broken**.
- Reproduction (pre-fix source): `uv run pytest -q tests/test_learner_blindness_relax_codex_review.py -k "later_turn
  or feedback_turn_inherits or earlier_turn_whose"` gave **3 failed**.
- Fixed tree: `uv run pytest -q tests/test_learner_blindness_relax_codex_review.py tests/test_learner_blindness_relax.py`
  gave **26 passed**.
- Targeted run, `uv run pytest -n 6 -q` on the files below: **958 passed, 0 failed** (155 s).
  - Added or changed: `tests/test_learner_blindness_relax_codex_review.py`
  - Stage tests: `tests/test_learner_blindness_relax.py`
  - Practice leakage and exam protection: `tests/test_practice_leakage.py`, `tests/test_exam_protection.py`,
    `tests/test_exam_protection_identity.py`
  - Reader tutor and RW1c: `tests/test_reader_rw1c_review.py`, `tests/test_reader_rw2b_fix15.py`,
    `tests/test_reader_tutor_retrieval.py`, `tests/test_reader_tutor_offers.py`,
    `tests/test_reader_tutor_switch_off.py`, `tests/test_library_ask_review.py`,
    `tests/test_reader_ca2_astra_handoff.py`, `tests/test_reader_ca2_astra_handoff_recovery.py`,
    `tests/test_reader_ca2_codex_rereview.py`, `tests/test_reader_ca2_codex_review.py`,
    `tests/test_reader_ca2_one_ask.py`
  - TE0 confidence events: `tests/test_teacher_te0_confidence_events.py`, `tests/test_teacher_te0_fix_round2.py`,
    `tests/test_teacher_te0_review_fixes.py`
  - Contracts: `tests/test_architecture.py`, `tests/test_desktop_rpc_contract.py`, `tests/test_mobile_allowlist.py`

These steps did not apply and were not run:

- Only `src/learnloop/reader_learner_state.py` and its test file changed.
- No config key, CLI surface, migration, DB or connection code, frontend or `src-tauri` changed.
- No new constant was added.

## Second re-review (Codex job `20261101-160205-68yc5y`, verdict REOPENED) and structural close

Codex reopened F1 a second time, again on the transitive provenance of stored tutor answer text that the Reader
learner state re-showed (`answer_shown`). The scenario was a cross-item feedback chain: attempt A, an explicit item
B, a later turn restating B's solution, and B then exam-protected. F2 and F3 stayed confirmed fixed.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | REOPENED: a stored answer can restate another item's solution through a cross-item feedback chain | closed structurally | step-0 commit (see the landing record) | `tests/test_learner_blindness_relax_codex_review.py::test_a_cross_item_feedback_chain_carries_no_answer`, `::test_the_module_never_reads_stored_answer_text`, and the earlier F1 reproductions, which now pass because no answer text is present |
| F2 | High | Unrelated switches disable the new state path's cold protection | confirmed fixed (no change) | `adb862f63e` | unchanged |
| F3 | Medium | Prior workbench traces are omitted from diagnosis provenance | confirmed fixed (no change) | `adb862f63e` | unchanged |

**What changed (stuck-loop rule, owner principle: include learner data when beneficial, leave it out when it is
noise).** The Reader learner state no longer re-shows stored tutor, practice or feedback answer text at all. It
carries:

- readiness in words;
- confidence events;
- recent attempt outcomes (result class, date, help);
- the learner's own question text from recent practice and feedback exchanges, filtered through
  `learner_protection` as before (`PastWork.evidence_reason` on the item and the attempt).

The query selects the question columns only, never `answer_md` or `source_context_json`. Removed: `answer_shown`,
`answer_left_out`, the `answers_left_out` count, `answer_source_refs`, `_thread_turns`, `_source_reason`,
`_decoded`, `ANSWER_SOURCES_UNKNOWN`, the `bound_item_id` parameter (it only suppressed answers), and
`practice_leakage.teaching_link_refs` (only this module used it). The tutor prompt's learner-state sentence and the
Reader prompt contract now say "their own questions … never the answers they were given". The learner's own attempt
answer was never part of the state, and still is not. The F2 session resolution in
`learnloop_sidecar.handlers.reader_tutor.learner_state` and the F3 trace fold are unchanged.

**Tests.** No stored answer text appears in any of these scenarios, before or after the protection changes:

- the held-out linked passage;
- the retrieved passage;
- the two-turn thread;
- the feedback thread;
- the cross-item chain.

Each entry has exactly `date`, `when` and `learner_question`. Learner questions and outcomes still show. A source
pin (`test_the_module_never_reads_stored_answer_text`) checks that the module selects no answer column and imports
none of the tutor's answer readers.

orchestrator ruling: F1 class closed by structural simplification (no stored answer text in Reader learner state)
