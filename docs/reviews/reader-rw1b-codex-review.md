# Reader workbench RW1b: Codex review and fixes (stage `reader-rw1b`)

Branch `reader/rw1b` (worktree `learnanything-merge4`), reviewed at `9fba44812`
(codex-job `20261017-154349-dk2L7y`). Codex reported 13 findings: 1 High, 12
Medium. The fixes are in `18472d5ac` (plus `bd6c37950` for an import-inventory gate fix). Each finding was reproduced first, with a
test that fails on `9fba44812`:

- backend: `tests/test_reader_rw1b_review.py`. 13 of its 16 cases fail on the
  stage tip, run against `git archive 9fba44812 src migrations` on `PYTHONPATH`.
  The other 3 guard behaviour that was already correct: the second F5 crash
  point, an unavailable Decider that spends no allowance, and F13's
  backend escalation;
- frontend: `apps/learnloop-tauri/src/screens/reader/rw1bReview.test.tsx`. All
  12 cases fail with the stage tip's sources.

No paid or live model call was made. Every test uses fakes.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Formative answers become numeric serving signals without a successor | fixed | `18472d5ac` | `test_f1_a_formative_gap_is_not_a_weak_prerequisite_signal`, `test_f1_a_formative_gap_brings_no_check_forward`. `text_gaps.contract.NON_SERVING_SOURCE_KINDS` (`reader_formative`, `workbench_text`) are left out of `field.signals.learner_gap_targets` and of the pipeline's sooner-check advance, whatever the switches say. Spec W1 calls a tier-2 signal that changes serving an algorithm successor, and §17 defers formative numeric signals. No such rows existed before RW1b, so the result is byte-identical to the base. Stage open question 1 is resolved to "no" |
| F2 | Medium | Concurrent routings exceed the daily paid-call cap | fixed | `18472d5ac` | `test_f2_two_routings_racing_for_the_last_call_admit_one`, `test_f2_two_speculations_racing_for_the_last_speculative_call_admit_one` (each uses a barrier-synchronized fake, with threads on their own connections), `test_f2_an_unavailable_decider_spends_no_allowance`. `reader_intent._reserve` counts and claims one `judgment_work_claims` row (`reader_intent_allowance:<day>:<routing>`) in one `BEGIN IMMEDIATE` transaction before the request is sent. Speculation's limit is 80% of the cap. A spend refusal releases the claim. No migration was needed: the table is WORKFLOW |
| F3 | Medium | Identical routing requests corrupt each other's ledger history | fixed | `18472d5ac` | `test_f3_identical_routings_keep_their_own_fates_and_corrections`. A routing's ledger question is now its own (left id = the routing id, left kind `reader_intent_routing`), and `input_hash` keeps the input's hash. `_head` follows the descendants of the routing's root row. The head read and the append share one write transaction |
| F4 | Medium | "Change" preserves the action it claims to replace | fixed | `18472d5ac` | `test_f4_change_reverts_the_routed_capture_its_commitment_and_its_request`, `test_f4_only_a_capture_routing_reverts`, and vitest "F4: change after a routed capture reverts it…". `reader.intent_outcome` gains `reverted` (with `annotationId`). It is allowed only for a routed preset or highlight. `reader_intent.revert_capture` tombstones the annotation (reason `intent_changed`), retires the commitment the capture made, and cancels the capture's synthesis request. Each step is idempotent. The frontend keeps each run's handle. "change" stops a pending Ask, closes the active-reading or another-way card, reverts a capture and cancels a running import (`cancelIngestBatch`). This supersedes the stage's deviation 5 and open question 5 |
| F5 | Medium | Reconstruction is not crash-idempotent | fixed | `18472d5ac` | `test_f5_a_crash_after_the_item_is_written_leaves_one_item` and `test_f5_a_crash_before_the_commitment_leaves_one_item_and_one_commitment`. A selection-scoped escalation now names its item after the question (`reader_quick_check.selection_item_id`), so a retry rewrites the same item. The commitment was already idempotent on `reader_reconstruct:<question>`. Section and inquiry escalations keep their random ids |
| F6 | Medium | Reopening an undone reconstruction falsely reports scheduled practice | fixed | `18472d5ac` | `test_f6_an_undone_reconstruction_is_never_reported_as_scheduled_again` and vitest "F6: …". `reconstruct_commit` raises `ReconstructUndone` when the question's commitment is stopped, and the RPC returns code `reconstruct_undone`. The card says "You undid this reconstruction earlier, so it won't be asked." and makes no call. Stage open question 6 ("no second try") is kept and now enforced |
| F7 | Medium | A crash can permanently lose a formative gap job | fixed | `18472d5ac` | `test_f7_a_failed_enqueue_leaves_the_self_check_unrecorded` and `test_f7_the_backlog_sweep_recovers_a_missed_answer_without_a_job`. `active_reading.record_action` commits the self-check, its `learner_card` verdict and the `reader_formative` job in one transaction. The worker is woken after the commit. `sweep_backlog` (`learnloop gaps run --backlog`) queues missed answers that have no job while `reader_formative.enabled` is on (new `reader_formative` count) |
| F8 | Medium | The advertised selection → Tab keyboard path does not work | fixed | `18472d5ac` | vitest "F8: selection, then Tab, focuses the palette…" presses Tab with no prior `?`. Tab from the reading surface (in either path, skim included) now focuses the palette's first action, so the arrows move through the actions and Enter presses the focused button instead of running an empty Ask |
| F9 | Medium | Transcript next-step questions leave the answer visible | fixed | `18472d5ac` | vitest "F9: a video transcript folds the next step…" uses the real `YouTubeWatchPanel` through `ReaderScreen` on a video card. The panel takes `fold` (the folded spans and the shared `NextStepFoldLine`). Folded cues show `···` and no words, with the dotted rule and "show" before the first one. The original-page cover was already wired (`coveredSpans`) |
| F10 | Medium | Failed source verification is presented as an empty library result | fixed | `18472d5ac` | vitest "F10: a verification that failed…" and "F10: a refused verification…". `anotherWayOutcome` reads `find_sources`' status. `ok` lands. `unverified: unavailable` is unreachable, `unverified: over_budget` is capped, and anything else fails with "Couldn't check what your books say about this." Each failure offers "try again" (`retryAnother`). The empty-result line appears only after a finished search |
| F11 | Medium | Cancelled "another way" results reopen themselves | fixed | `18472d5ac` | vitest "F11: a late result…" and "F11: a late failure…". `closeAnother` (close and cancel) advances the request key, so a late success or failure is dropped |
| F12 | Medium | Enter-only routing disappears from usage and correction metrics | fixed | `18472d5ac` | vitest "F12: with speculation off…", "F12: a speculative routing that fell back…" and "F12: a speculative routing still in flight…"; pytest `test_f12_an_enter_only_use_and_its_correction_are_counted` and `test_f12_a_fate_asked_while_the_routing_runs_lands_when_it_finishes`. Every routing that runs reports `used` (routed or fallback, Enter or speculative). Every speculative routing that is not taken gets `discarded`, including a fallback and one still in flight: the sidecar keeps the fate and the worker records it when the routing lands. The report's correction denominator is the used routings the Decider chose (`status = routed`) |
| F13 | Medium | Formative questions cannot be added to practice | fixed | `18472d5ac` | vitest "F13: an answered question offers 'add to practice'…" and pytest `test_f13_answering_makes_no_item_and_add_to_practice_makes_exactly_one`. The card offers "add to practice" once the question is answered (through the existing `reader.escalate_authored_question`). It then shows "Added to your practice", and the self-check and "don't bring this back" are hidden, since the row refuses them once escalated. With no linked learning objective it says so |

**Codex's "claims that don't hold":** each one is addressed by the findings
above. The stage record (`reader-workbench-RW1b.md`) is corrected in §1.3, §3
item 5, §4 (successor) and §8 questions 1, 5 and 6.

**No rejections.** Two of the fixes go against defaults the stage had
recorded: open question 1 (yes → no) and open question 5 (no → yes). Each new
behaviour follows the spec's text: W1 for F1 and §4.2's "change cancels it"
for F4, which UX §4.1's "change while it runs" also supports.

## Files

- Backend: `src/learnloop/reader/reader_intent.py` (allowance, ledger identity,
  `revert_capture`), `src/learnloop_sidecar/handlers/reader_intent.py`
  (deferred fates, `reverted`, `record_action`, `reconstruct_undone`),
  `src/learnloop/reader/active_reading.py`, `src/learnloop/reader/reader_quick_check.py`
  (`selection_item_id`), `src/learnloop/reader/reader_report.py`,
  `src/learnloop/diagnosis/text_gaps/{contract,pipeline,jobs,sources}.py`,
  `src/learnloop/field/signals.py`.
- Frontend: `screens/reader/{useIntentBox.ts, useActiveReading.ts,
  ActiveReadingCard.tsx, YouTubeWatchPanel.tsx}`, `screens/ReaderScreen.tsx`,
  `api/client.ts`. No `src-tauri` change: the passthrough is generic.
- Tests: `tests/test_reader_rw1b_review.py` (new, 16 cases),
  `screens/reader/rw1bReview.test.tsx` (new, 12 cases),
  `tests/test_reader_intent.py` (the day's count now reads the reserved
  allowance on the routing's clock), `tests/test_learner_text_gaps_flow.py`
  (the backlog report's new `reader_formative` count).
- References regenerated (commit labels and the config leaves' line citations;
  schema head still 208, no migration change).

## Gate

Run in the worktree with `TMPDIR=fixtures-local/tmp` and `uv run --no-sync` after the install. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock`. Fixes are in `18472d5ac`, followed by `bd6c37950` (one import moved to module level) and `4040b14e8` (references).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **24 kept**, 0 broken |
| `pytest -n auto` (full suite) | **13,038 passed, 2 xfailed**, 0 failed (14 min 57 s, on `4040b14e8`). Stage tip: 13,022, so +16 (the new review file). The first run, on `18472d5ac`, had 1 failure, `test_architecture.py::test_function_local_domain_imports_match_the_frozen_edge_inventory`, because `revert_capture` imported `curriculum.commitments` inside a function. Fixed in `bd6c37950` (module-level import, as `active_reading` has); that test passed alone, then in the full rerun |
| `pytest -m durability` | **107 passed**, 12,933 deselected (1 min 56 s, on `4040b14e8`) |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | **120 files, 971 tests passed**. Stage tip: 959, so +12 (`rw1bReview.test.tsx`) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check` | not needed: nothing under `src-tauri` changed (`reader.intent_outcome` uses the generic passthrough) |
| `db_generate_reference.py`, `db_validate_reference.py` | regenerated (schema head 208, 327 table notes, 873 configuration leaves); errors [] |
| Snapshots, CLI help, RPC pins, `test_coordinated_migrations.py`, `test_table_roles.py` | pass (in the full suite); no config, CLI or migration change |
| `git diff --check` | clean |
