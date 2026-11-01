# Curriculum C5: Codex review and fixes

**Stage:** `curriculum-c5-notes-as-learner-text`, branch `curriculum/c5-notes-as-learner-text` (worktree
`learnanything-dl2`). **Review:** Codex (gpt-6.1-sol), job `20261101-181024-WwvRyO`: five findings (four High, one
Medium). Each was reproduced with a failing test first (all nine new tests failed on `6cb6b4bed4` for the reason
the finding names), then fixed.

**No paid or live call was made.** Every model is a fake (`tests/text_gap_fakes.py`, plus two new plan doubles
in the test file: one that sends each answer as a physical request through the request gate, and one whose
inference raises `ChatGPTPlanUsageExhausted`). The owner's real `tend` was never run and no note of the
owner's was opened: every notes test uses C2's FAKE `tend` over synthetic notes in the test's tmp directory. No
owner vault, `~/.config/learnloop` or tracked working fixture was touched.

## Review

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Note-derived beliefs escape the plan-only boundary | **fixed** | `906e471141` | `test_f1_a_notes_belief_never_becomes_a_candidate_nor_leaves_the_plan_through_an_ordinary_gap` |
| F2 | High | Stored snapshots bypass the current notes allowlist | **fixed** | `906e471141` | `test_f2_a_note_outside_the_current_allowlist_is_never_queued_or_read` |
| F3 | High | Revoking consent does not stop an in-flight note reading | **fixed** | `906e471141` | `test_f3_revoking_consent_before_dispatch_sends_nothing`, `test_f3_hiding_the_link_between_requests_stops_the_reading_and_writes_nothing`, `test_f3_switched_off_before_the_final_write_writes_nothing`, plus a gate assertion in `test_gc1_exam_sentinels_never_reach_the_gap_model_via_a_notes_context` |
| F4 | High | Mixed queues can bypass metered spend caps | **fixed** | `906e471141` | `test_f4_mixed_queues_keep_metered_routes_metered[True]` and `[False]`, `test_f4_the_dry_run_plan_names_the_notes_route` |
| F5 | Medium | Runtime plan outages permanently fail note jobs | **fixed** | `906e471141` | `test_f5_a_plan_outage_at_inference_waits_and_never_fails_the_note` |

All tests are in `tests/test_notes_as_learner_text.py`. None of the findings was rejected.

### F1: nothing derived from a note is kept where non-plan consumers read it

The finding reproduced: a plan reader that echoed a synthetic sentinel into `belief_statement` produced a
holding-pen candidate carrying the sentinel. A later ordinary gap on the same LO then sent it to its pair judges.

Instead of tagging provenance and filtering it in every consumer of the holding pen and the gap table (the
router's card, the learner context the MCP server serves, library asks, passage cues, the diagnoser, every
later gap's pair judges), the fix keeps the note-derived words out of those stores altogether:

- `actions.record_belief`, the one writer of holding-pen candidates, never creates a candidate from a
  `learner_note` text. A belief that matches an entry that already exists (judged on the plan) is still
  recorded as a sighting, which bumps that entry's count without writing any words. Otherwise the belief is
  `signal_only` with reason `never_a_candidate_from_a_note`. This parallels C5's existing
  `never_drafted_from_a_note` rule for prerequisites: a note is never a generation input (§10.2).
- `pipeline._log`: for a note, the gap row's `named_json` keeps its keys with empty values, and the detail
  records `named_words: not_kept_for_a_note`. The row still keeps the kind and the vault's own target (an
  existing LO or a registry entry), so the note still steers routing. The model's words remain only in the
  job's checkpoint, which only the plan-only pipeline reads.
- `provenance.reading_record` refuses a `learner_note` text. This makes explicit the reviewer's point that the
  record would have lost the note's provenance; nothing written from a note needs one now.
- The regression test runs an ordinary gap afterwards, read off the plan by the gap judge's route and the
  Decider, and checks that every payload it sent, the holding pen, the gap table and `named_gaps_for_card`
  carry no sentinel.

### F2: the allowlist as configured now

`note_gaps.linked_notes` now drops any effective link whose snapshot path is outside `notes.tend.paths` as it
is configured now (`notes_tend.allowed`, C2's rule). That one function feeds the queue (`enqueue_learner_notes`,
the backlog sweep), the adapter (`note_text`) and the new refusal check (F3). As a result, a note excluded after
it was linked is not queued, has no text, and its already-queued job is skipped unread.

### F3: a request gate for every note reading

`pipeline.NoteGate` is installed by `process_learner_text` for every note, using `gate_model_requests` and
composing with any outer gate, such as RW5a's figure gate. It is asked before **every physical request** and,
inside the gap row's write transaction, **before the row is written**. Each time it reloads the vault from disk
and asks `sources.learner_note_refusal` → `note_gaps.refusal` whether all of these still hold:

- `notes.gaps_enabled`, `notes.enabled` and `learner_text_gaps.enabled` are on, and tend is present;
- the snapshot is still a standing link (not hidden or superseded);
- the snapshot is inside the current allowlist;
- nothing it is linked to is protected now.

The first refusal raises `NoteReadingStopped`. It is a `BaseException`, like C2's `NotesSwitchedOff` and
RW5a's `FiguresChanged`, so no judge's `except Exception` can turn it into a failed reading and carry on. The
job ends `skipped` ("stopped: …"). C5's existing requeue puts it back in the queue when the note is linked
again (tested with hide, then *undo*).

### F4: the note's own route in the budget

A note's reading, its pair verdicts and (unreachable for a note) "needed?" are now admitted on
`note_link_judge` (`contract.NOTE_ROUTE`) through `judges.gap_route`, while `judges.READING_NOTE` is set.
Before, they were admitted on `learner_gap_reader` / `learner_gap_judge`. The plan's client is therefore never
registered under a route an ordinary gap uses. With one command budget across a mixed queue, in either order,
the ordinary gap's metered reader stays `metered`: it is charged, capped and its physical retries are
admitted. The note's route stays `subscription`. `jobs.plan` (the `gaps run --dry-run` plan) now names the
`note_link_judge` route whenever notes may be read (the opt-in on, or a note job queued). `register_llm`'s
first-registration-wins rule itself is unchanged: every other route still has one client per run.

### F5: plan outages at inference wait

- `judges.read_text` re-raises `AIProviderUnavailable`, which includes `ChatGPTPlanUsageExhausted`, sign-in and
  eligibility errors, for a note instead of turning it into a failed reading. Every other kind behaves as
  before.
- `_judge_all` runs a note's pair verdicts with `AIProviderUnavailable` among `judge_pairs`' stop
  exceptions, so the claim is released and the pair left `not_run`, and then raises `ReadingWaits`.
- `process_learner_text` turns an `AIProviderUnavailable` from a note's reading into `ReadingWaits`.

The job is therefore released with its attempt refunded and backed off by `BACKOFF_SECONDS`, however many
times. It never becomes a failed gap. The test runs `MAX_ATTEMPTS + 2` outages in the reading, then one in the
pair verdicts, and then reads the note once the plan is back.

### The "claims that don't hold"

Each of the review's "claims that don't hold" is covered by the fixes above:

- C2's transport rules: current-folder authorization (F2) and per-request revocation (F3).
- Nothing derived from a note leaves the plan: no candidate and no named words (F1).
- Waiting never fails a note: outages at inference wait too (F5).
- A hidden note is never read: hiding mid-reading stops it before the next request and the write (F3).

The stage review's decisions 6 and 8 are amended to match.

## Constants

None new. Bounds reused: `jobs.BACKOFF_SECONDS` and `MAX_ATTEMPTS`. `NOTE_ROUTE` is the existing routing task
`note_link_judge`. No config key, migration, schema, table role or frontend change.

## Gate (this step; targeted, memory-capped)

Every pytest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at
`-n 6`, one test command at a time, with `TMPDIR` in the session scratchpad outside the worktree. No live model
call was made and the real `tend` was never run.

| Step | Result |
|---|---|
| Reproduction: the 9 new tests on the unfixed tree (`-k test_f`) | **9 failed**, each for the reason its finding names (candidate holds the sentinel; excluded snapshot still listed; `done` instead of `skipped` (×3); `learner_gap_reader` billed `subscription`; `note_link_judge` unregistered; route missing from the plan; `ReadingDeferred: the note's reading failed`) |
| `tests/test_notes_as_learner_text.py` after the fixes | **23 passed** |
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **37 kept, 0 broken** |
| Targeted set (55 files, listed below): every test file importing a changed module (`text_gaps` pipeline, jobs, judges, actions, provenance, sources, contract; `note_gaps`; the gap CLI), the C2 notes tests, the plan-first transport and route tests, and the contract tests (architecture, CLI help snapshot, serializer snapshot, desktop RPC contract, mobile allowlist, table roles, coordinated migrations, tracked fixture databases, config refactor, the two source-kind widenings and the C5 migration) | **1307 passed, 2 xfailed, 0 failed** |
| `tests/test_notes_as_learner_text.py --durable-sqlite` (production pragmas and WAL; the gate's check runs inside the write transaction) | **23 passed** |
| Frontend, `src-tauri`, schema | not run: no file changed there (no migration, no DB reference change) |

Targeted test files:

- `tests/test_ad23_fix_review.py`
- `tests/test_architecture.py`
- `tests/test_cli_help_snapshot.py`
- `tests/test_codex_lockdown_round3.py`
- `tests/test_config_refactor.py`
- `tests/test_coordinated_migrations.py`
- `tests/test_desktop_rpc_contract.py`
- `tests/test_diagnosis_input_provenance.py`
- `tests/test_diagnosis_input_provenance_landing.py`
- `tests/test_figure_predictions.py`
- `tests/test_figures_codex_review.py`
- `tests/test_figures_fix_round2.py`
- `tests/test_figures_fix_round3.py`
- `tests/test_figures_fix_round4.py`
- `tests/test_figures_scope_redesign.py`
- `tests/test_figures_show_me.py`
- `tests/test_figures_show_me_codex_review.py`
- `tests/test_figures_switch_off.py`
- `tests/test_held_grade_composition.py`
- `tests/test_hint_feedback_texts.py`
- `tests/test_hint_feedback_widening.py`
- `tests/test_hint_h2b_review.py`
- `tests/test_judge_routes.py`
- `tests/test_learner_note_source_kind_migration.py`
- `tests/test_learner_text_gaps.py`
- `tests/test_learner_text_gaps_composition.py`
- `tests/test_learner_text_gaps_flow.py`
- `tests/test_learner_text_gaps_rereview.py`
- `tests/test_learner_text_gaps_review.py`
- `tests/test_learner_text_source_widening.py`
- `tests/test_mcp_c1a_narrow.py`
- `tests/test_mobile_allowlist.py`
- `tests/test_notes_as_learner_text.py`
- `tests/test_notes_linked.py`
- `tests/test_notes_never_read.py`
- `tests/test_plan_first_transport.py`
- `tests/test_plan_first_transport_grant_scope.py`
- `tests/test_plan_first_transport_offer_grants.py`
- `tests/test_plan_first_transport_offer_grants_r5.py`
- `tests/test_plan_first_transport_paid_roles.py`
- `tests/test_reader_formative_texts.py`
- `tests/test_reader_rw1b_review.py`
- `tests/test_reader_rw3b_review_fixes.py`
- `tests/test_required_method_round3_review.py`
- `tests/test_scoreboard.py`
- `tests/test_sidecar_close_cancels_jobs.py`
- `tests/test_sidecar_serializer_snapshot.py`
- `tests/test_surfaced_belief_corrections.py`
- `tests/test_t6_followup_composition.py`
- `tests/test_table_roles.py`
- `tests/test_tier1_decider.py`
- `tests/test_tracked_fixture_databases.py`
- `tests/test_ux_phase4_landing.py`
- `tests/test_workbench_text_gaps.py`

## Open items for the landing

- The job's checkpoint (`learner_text_gap_jobs` payload) still holds the plan's reading of a note, including
  its named words, so that a retry reuses it. Only the plan-only pipeline reads it. No consumer that sends
  elsewhere reads job payloads, so no change was made.
- C2's own surfaces (the Reader's `›` marks, path lines) check the allowlist when a note is linked
  (`note_links`), and do not refilter stored links against a narrowed
  allowlist. That is C2's scope, not C5's, and it was left unchanged here. Only the gaps input is filtered (F2).
