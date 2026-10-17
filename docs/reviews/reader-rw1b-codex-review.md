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

## Re-review (codex-job `20261017-171207-Xoiq5R`, range `9fba44812..reader/rw1b`)

The re-review confirmed F1 (High) as fixed and reopened the stage on two new
Medium findings, F14 and F15. Both were reproduced on `80c565ef4` (the review
record's tip) with `tests/test_reader_rw1b_rereview.py`, a new file with 7 cases.
6 of them failed before the fix. The seventh,
`test_f15_reverting_the_sharing_capture_keeps_the_original_and_cancels_last`,
guards the new hold rule from the other side: on the old code, reverting the
second capture found no request, so nothing was cancelled. The fixes are in
`6c63eceb3`, and the references were regenerated in `fbd198c5a`. No migration
was needed: a capture's hold on a request is its outbox row's `target_ref`, which
the drain has always written. No paid or live model call was made.

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Formative answers become numeric serving signals | confirmed fixed (re-review) | `18472d5ac` | Codex checked all eight switch combinations in memory. Nothing changed |
| F14 | Medium | Reverted captures can enqueue synthesis later | fixed | `6c63eceb3` | `test_f14_a_capture_reverted_before_its_drain_enqueues_nothing`, `test_f14_a_failed_conversion_retried_after_the_revert_enqueues_nothing`, `test_f14_a_revert_racing_a_drain_waits_for_it_and_cancels_what_it_enqueued` (a revert thread starts while the conversion is inside its transaction). The revert's tombstone (`delete_intent`, reason `intent_changed`) is the persisted cancellation. `reader_capture._default_convert` runs in one `Repository.atomic()` (`BEGIN IMMEDIATE`) write transaction. In it, the conversion reads whether that tombstone stands (`Repository.capture_reverted`, which honours an undo), enqueues, and records the request as the outbox row's `target_ref`. A reverted capture converts to no work, so the row goes to `done` with no request. `revert_capture` (tombstone, retire, cancel) is also one write transaction. A revert racing a drain therefore either lands first, and nothing is enqueued, or waits and then cancels what the drain enqueued |
| F15 | Medium | Capture undo cancels shared synthesis and blocks later captures | fixed | `6c63eceb3` | `test_f15_reverting_the_original_capture_keeps_work_another_capture_holds`, `test_f15_reverting_the_sharing_capture_keeps_the_original_and_cancels_last`, `test_f15_a_later_capture_revives_cancelled_work`, `test_f15_a_later_capture_keeps_running_work_its_revert_flagged`. A revert now finds every request its capture holds: the one it made, plus any its outbox row converted onto. It cancels a request only when `Repository.reader_request_still_held` says no other capture holding it stands, meaning one whose `target_ref` names it, or the request's first capture, with no standing delete. A request no capture made (an explicit `reader.enqueue_request`) always counts as held. A capture's conversion enqueues with `revive_cancelled=True`. A `cancelled` row goes back to `queued` with its lease and completion cleared, and a running row flagged for cancellation has the flag cleared. The `reader.enqueue_request` RPC and `retry` keep their old behaviour |

**No rejections.** Out of scope: a capture deleted normally (not by "change")
before its drain still converts to synthesis. That is the base's behaviour, and
the conversion skips only reverted captures. Such a capture does not count as
holding shared work.

### Re-review gate

Run in the worktree with `TMPDIR=fixtures-local/tmp` and `uv run --no-sync` after
the install. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock`
on `fbd198c5a`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **24 kept**, 0 broken (`reader_intent` now imports `reader_capture` at module level, adding no function-local import) |
| `pytest -n auto` (full suite) | **13,045 passed, 2 xfailed**, 0 failed (19 min 51 s). Previous gate: 13,038, so +7 (the new re-review file) |
| `pytest -m durability` | **107 passed**, 12,940 deselected (1 min 56 s) |
| `tests/test_reader_rw1b_rereview.py --durable-sqlite` | 7 passed (WAL and production pragmas, including the race case) |
| Frontend (npm typecheck/test/build), `cargo check` | not needed: nothing under `apps/` changed |
| `db_generate_reference.py`, `db_validate_reference.py` | regenerated (commit labels and the config leaves' line citations; schema head 208); errors [] |
| `git diff --check` | clean |

## Fix round 3 (orchestrator, after final verify)

Codex's final verify (codex-job `20261017-174618-UNt9pX`, at `fb80d9c7c`)
confirmed F1 (High) and F15 as fixed. It reopened F14 and raised one new Medium
finding, F16. Both were reproduced on `fb80d9c7c` with
`tests/test_reader_rw1b_final_verify.py`, a new file with 8 cases, and **all 8
fail there**. That run used `git archive fb80d9c7c src migrations tests
pyproject.toml` with the new file copied in, because the worktree's
`pythonpath = ["src"]` would shadow a `PYTHONPATH` override. The fixes are in
`527e3fb1d`, and the references were regenerated in `91549192f`. **No
migration and no schema change.** No paid or live model call was made.

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F14 | Medium | A revert after an undone revert lets synthesis run (reopened) | fixed | `527e3fb1d` | `test_f14_a_revert_after_an_undone_revert_converts_to_no_work` (Codex's repro: capture, revert, restore naming that delete, revert, drain. On `fb80d9c7c` the second revert wrote no tombstone, 1 ≠ 2), `test_f14_revert_restore_revert_then_a_retried_conversion_enqueues_nothing` (on `fb80d9c7c` a live request was queued), `test_f14_revert_restore_revert_restore_converts` (converts, one queued request; on `fb80d9c7c` it failed on its F16 assertion, a mapping to the retired commitment). `revert_capture` now asks `Repository.capture_reverted` inside its write transaction. That is the predicate the conversion reads: a revert tombstone with reason `intent_changed` that no undo names. If none stands, even when an earlier one was undone, the revert writes a new tombstone and cancels as F15's hold check allows. The revert and the conversion read one predicate |
| F16 | Medium | Revived synthesis uses the reverted capture's instructions and commitment | fixed | `527e3fb1d` | `test_f16_captures_with_different_instructions_never_share_or_revive` (Codex's repro: A "emphasize the matrix algebra", drained, reverted; B "emphasize the geometry". Now there are two requests. A's stays cancelled. B's carries B's annotation and commitment, and the model is told only B's instructions. The one commitment mapping is B's, none is A's. On `fb80d9c7c` there was 1 request), `test_f16_a_same_instruction_revival_rebinds_to_the_reviving_capture` (the same instructions, spaced differently, revive one request, rebound to B's annotation and commitment; the mapping is B's), `test_f16_a_running_revival_lands_on_the_reviving_capture`, `test_f16_reverting_the_bound_capture_of_shared_work_rebinds_it`, `test_f16_a_key_without_instructions_is_unchanged` (on `fb80d9c7c` each failed: A's binding, or no `instructions` parameter) |

**How F16 is fixed.**

- **Identity.** A capture's instructions are its annotation's `learner_text`,
  which is what `model_synthesis` gives the model. They are now part of its
  request's key. `reader_capture._enqueue_for` reads them from the annotation
  head inside the conversion's transaction and passes them to
  `rr.enqueue_request(instructions=...)`. `rr.request_key` folds
  `instructions_hash`, the sha256 of the instructions with whitespace
  collapsed (`rr.normalized_instructions`), into the canonical JSON **only
  when there are some**. This uses the existing `request_key` column and its
  unique index, with no new column, index or migration. A key without
  instructions is byte-identical to before. That covers every existing row, a
  capture with no note, and the explicit `reader.enqueue_request` RPC, which
  passes none. The new key cannot collide with a key without instructions.
- **Revival.** `Repository.enqueue_reader_request(revive_cancelled=True)` only
  revives a row whose key matches, so the instructions match. It now sets the
  row's `annotation_id` and `commitment_id` to the reviving capture's.
- **A held request whose bound capture is reverted.** F15 keeps a request
  that another capture still holds. When the request was bound to the
  reverted capture, `revert_capture` now rebinds it to the latest standing
  holder (`Repository.reader_request_standing_holder`, then
  `rebind_reader_request`).
- **Landing.** `_land_proposals` re-reads the row's binding when it lands, so
  a running request revived after it was claimed maps to the reviving capture.
  It never proposes a commitment mapping onto a `stopped` commitment. A retired
  one is what a reverted capture leaves, and a restore does not un-retire it.
  An unknown commitment keeps the old behaviour.

**Base behaviour.** Request rows change only on the revert, revive and
landing paths, plus one case named by the ruling ("captures with different
instructions never share"): two captures of one passage and preset with
*different, non-empty* notes used to share one request. The second capture's
note was silently ignored, and its commitment got no mapping. Now each gets
its own request. Kill switches off: the prompt contract and the RPC contracts
are unchanged (contract pins pass). With `reader_intent` off nothing reverts,
so nothing revives or rebinds. A stopped commitment could only gain a mapping
on the base if the learner stopped it before its synthesis ran. That mapping
is now withheld.

### Fix round 3 gate (targeted, per the owner's rule of 2026-10-17)

The full suite, the whole durability lane and the whole vitest run are left
to the landing gate. Run in the worktree with `TMPDIR=fixtures-local/tmp`,
using `uv run --no-sync` after the install.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **24 kept**, 0 broken (`reader_requests` imports `curriculum.commitments` at module level, as `reader_capture` and `reader_intent` already do) |
| `pytest -n auto`, 61 files | **1,421 passed**, 0 failed (68 s): every `tests/test_reader_*.py` and `tests/test_sidecar_reader*.py` (the RW1b review 16, re-review 7 and final-verify 8 files included), and every other file that exercises `reader_capture`, `reader_requests`, `reader_intent` or the touched repository methods (`test_annotations`, `test_codex_output_schema`, `test_exam_protection`, `test_ingest_jobs`, `test_judge_routes`, `test_keep_local_retired`, `test_mobile_allowlist`, `test_p3_journeys`, `test_practice_proposal_caller_columns`, `test_reread_safety`, `test_salience_firewall`, `test_structured_transport_parity`). Also the contract pins: `test_architecture`, `test_table_roles`, `test_coordinated_migrations`, `test_desktop_rpc_contract`, `test_sidecar_contract`, `test_sidecar_serializer_snapshot`, `test_cli_help_snapshot`, `test_reference_check_binding`, `test_reference_gate_imports` |
| `tests/test_reader_rw1b_final_verify.py tests/test_reader_rw1b_rereview.py --durable-sqlite` | 15 passed |
| `db_generate_reference.py`, `db_validate_reference.py` | regenerated (commit labels, the config leaves' line citations, the new repository methods' notes; schema head 208, 327 table notes); errors [] |
| Frontend, `cargo check` | not needed: nothing under `apps/` changed |
| `git diff --check` | clean |

## Fix round 4 (orchestrator, after verify 20261017-180320-JrVMYw)

Codex's verify of round 3 (codex-job `20261017-180320-JrVMYw`, at `9714a4a33`)
confirmed F14 as fixed and reopened F16 (Medium) with four interleavings
through the real drain. All four were reproduced on `9714a4a33` with
`tests/test_reader_rw1b_fix_round4.py`, a new file with 10 cases. **6 of them
fail there**, run the way round 3 ran (`git archive 9714a4a33 src migrations
tests pyproject.toml` with the new file copied in). The other 4 guard
behaviour that must not change. The fix is in `c1ec76c7d`, and the references
were regenerated in `c1a9bccfa`. **No migration and no schema change.** No
paid or live model call was made.

The interleavings are deterministic, with no timing and no sleeps. The
interfering write (a revert or a revival) runs at a seam of the landing:
`RR._stopped`, `Repository.get_reader_request` after the model returned, or
the fake model call. It runs right there when the database would let another
writer commit at that point (a `BEGIN IMMEDIATE` probe with no busy wait).
Otherwise it runs right after the landing commits. On `9714a4a33` every seam
lets it run mid-landing. On the fix, every landing seam is inside the landing's
write transaction, so the write runs after it. Each test also asserts that its
seam was reached.

| ID | Case | Verdict | Commit | Test, and the result on `9714a4a33` |
|---|---|---|---|---|
| F16 | (a) A and B share a request. Landing reads A's binding, a revert of A rebinds the request to B, then landing finds A's commitment stopped and maps nothing | fixed | `c1ec76c7d` | `test_a_revert_after_the_binding_read_still_maps_the_holder`: B's commitment had 0 mappings (expected 1) |
| F16 | (b) A revert of A right after the stopped-check maps the proposal onto stopped A, though the request is bound to B | fixed | `c1ec76c7d` | `test_b_a_revert_after_the_stopped_check_moves_the_mapping`: B 0 mappings, A 1 |
| F16 | (c) A is reverted during the model call (the request is flagged), then B revives it between landing's binding read and its writes | fixed | `c1ec76c7d` | `test_c_a_revival_during_landing_ends_mapped_to_the_reviving_capture`: completed with B 0 mappings, and nothing left to run |
| F16 | (d) A legacy running request (unhashed key, instructions "matrix algebra") is reverted, then revived by a no-note capture with the same key | fixed | `c1ec76c7d` | `test_d_a_no_note_capture_never_revives_a_legacy_request_asking_something_else`: the legacy row completed on B with the old instructions (`complete` ≠ `cancelled`). `test_d_a_legacy_rekey_that_collides_takes_a_key_no_enqueue_computes`: 2 rows, not 3 (it was revived) |
| F16 | Ruling 2: a revert of a COMPLETED shared request | fixed | `c1ec76c7d` | `test_a_revert_of_a_completed_shared_request_moves_its_commitment_mapping`: still bound to A, with the mapping on A's stopped commitment |
| guard | A compatible no-note revival keeps its exact key; a completed request no one else holds is left as it is; an explicit cancel of a running request still lands; the landing writes the row the drain wrote | passes on both | `c1ec76c7d` | `test_d_a_compatible_no_note_revival_keeps_its_exact_key`, `test_a_revert_of_a_completed_request_nobody_else_holds_leaves_it`, `test_an_explicit_cancel_of_a_running_request_still_lands`, `test_the_landing_writes_the_drains_result` |

Each failing case now ends with the request bound to live B. B's commitment
has exactly one mapping, and A's stopped commitment has none. In (c) and (d)
the model was given B's instructions for the work that landed: the same
instructions in (c), and B's empty ones in (d), where the legacy request's
output was discarded and B got its own request.

**How it is fixed.**

- **Landing serializes with binding changes (ruling 1).** The model call
  stays outside any transaction. `_land_proposals` then runs one
  `Repository.atomic()` (`BEGIN IMMEDIATE`) transaction, which does four
  things:
  - it re-reads the request's binding and its commitment's status;
  - it authors the proposed source object and the `new_object` mapping for
    the current annotation;
  - it writes the commitment mapping only when the current commitment is not
    stopped;
  - for a request the drain claimed, it marks the request complete (fenced
    on the claimed `lease_epoch`).

  Its result is the dict the drain used to write, and the drain's own write
  after the seam returns then matches nothing (`test_the_landing_writes_the_drains_result`).
  Revert, rebind and revival already run in write transactions, so each one
  lands wholly before the landing or wholly after it. No mapping decision
  reads a binding outside that transaction.
- **A request a revert cancelled while it ran discards its result.** Such a
  request is still flagged at landing: a revival clears the flag, and a
  holder would have been rebound to. Its bound capture has a standing revert
  tombstone. It resolves `cancelled` with nothing landed (no source object,
  no mapping), and the drain skips it, as it skips a request cancelled
  before its claim (`LandingDiscarded`). On the base a flagged running
  request still landed. An explicit `reader.cancel_request` of a running
  request, with no revert, still lands as before. This is how (c) ends right:
  the revert-cancelled run is discarded and B's revival makes the request
  runnable again, bound to B.
- **A binding change after completion reconciles (ruling 2).** In its write
  transaction, `revert_capture` now handles a `complete` request that is
  bound to the reverted capture while another standing capture holds it. It
  rebinds the request to that holder (`RR.rebind_completed`) and moves the
  undecided commitment mapping from the reverted capture's commitment to the
  holder's live one (`Repository.repoint_mapping_proposal`, an UPDATE of
  `target_ref`). It adds a mapping only when the result has none to move,
  and records it in the result (`append_reader_request_proposal`). It never
  adds a second one. A decided mapping is the learner's and stays. The
  mapping table (`canonical_mapping_proposals`, WORKFLOW) already allowed
  this, so no schema change was needed. **The base never revives a completed
  request, and that is kept.** A later capture of the same passage and
  instructions reuses a completed result without a mapping of its own, as
  two sharing captures always have.
- **Legacy rows (ruling 3).** A revival (`rr.enqueue_request` with
  `revive_cancelled=True`, inside the conversion's write transaction) now
  compares the row's effective instructions with the reviving capture's,
  after `normalized_instructions`. The effective instructions are the bound
  annotation's head `learner_text`, which `model_synthesis` gives the model
  (`rr.annotation_instructions`, now shared by both). If they differ, the
  row is not revived:
  - it is re-keyed to the hashed key its own instructions give it
    (`Repository.rekey_reader_request`, an UPDATE of `request_key`);
  - it keeps its status and its cancel flag, so a running one discards its
    result on landing;
  - the capture gets a fresh request under its own key.

  On a collision, when that hashed key already belongs to another row, the
  legacy row takes `<hashed key>#legacy:<its id>`. No enqueue computes that
  key, so the row is never reused or revived again. No-note captures with no
  conflict keep their exact key. The check applies to any revivable row, but
  it can only differ from before for a legacy row or for an annotation whose
  text was edited after its enqueue.

**Base behaviour.** Request rows change only on the revert, revive and
landing paths. With the kill switches off nothing reverts, so nothing is
re-keyed, discarded or reconciled. The landing writes the same rows with the
same values as before. The only differences are that its writes commit
together and that the request completes inside the same transaction. The
prompt and RPC contracts are unchanged (the contract pins pass).

**Open questions (with the default taken).**

1. A no-note capture that *shares* a live legacy request (queued or running,
   not cancelled), as opposed to reviving it, still shares it, as on the
   base. Ruling 3 covers revival only. **Default: unchanged.** If A is later
   reverted, the request is rebound to the no-note capture. A run that has
   already started then lands with A's instructions.
2. Should an explicit `reader.cancel_request` of a running request also
   discard its result at landing, as `cancel_reader_request`'s docstring
   suggests ("flagged so the worker stops")? **Default: no.** That would
   change base behaviour with the switches off. Only a revert-cancelled run
   is discarded.
3. The reconcile moves only the commitment mapping. The source object's
   `new_object` mapping keeps the annotation it was landed for.
   **Default: kept.** The ruling names the commitment mapping, and that
   proposal records the capture the result was made for.

### Fix round 4 gate (targeted, per the owner's rule of 2026-10-17)

Run in the worktree with `TMPDIR=fixtures-local/tmp`, using `uv run
--no-sync` (the install from round 3 was reused). The full suite, the whole
durability lane and the whole vitest run are left to the landing gate.

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | **24 kept**, 0 broken (`reader_intent` now imports `reader_requests` at module level) |
| `pytest -n auto`, 63 files | **1,434 passed**, 0 failed (68 s). These are round 3's 61 files (every `tests/test_reader_*.py`, now including the new round-4 file, and `tests/test_sidecar_reader*.py`, plus the listed callers and contract pins), with `tests/test_source_objects.py` added because it exercises the mapping-proposal methods |
| `tests/test_reader_rw1b_fix_round4.py tests/test_reader_rw1b_final_verify.py tests/test_reader_rw1b_rereview.py --durable-sqlite` | 25 passed (WAL and production pragmas; the interleaving probe holds under WAL too) |
| Fail-first on `9714a4a33` | 6 of 10 fail, as in the table above; the 4 guards pass |
| `db_generate_reference.py`, `db_validate_reference.py` | regenerated (commit labels, the config leaves' line citations, and the notes for `repoint_mapping_proposal` and the other new repository methods; schema head 208, 327 table notes); errors [] |
| Frontend, `cargo check` | not needed: nothing under `apps/` changed |
| `git diff --check` | clean |
