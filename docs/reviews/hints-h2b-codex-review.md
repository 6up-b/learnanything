# Adaptive hints H2b: Codex review and fix round

Stage `hints-h2b`, branch `hints/h2b`. Codex reviewed `5b2efaf24..e02b62c37`
(job `20261018-101335-VI9Wfm`). It found 2 High and 5 Medium findings. The fix
round reproduced each finding with a test that failed before the fix, then
fixed it. All seven are fixed and none was rejected. No live or paid model
call was made; every model-backed path is tested with fakes. There is no new
migration and no new config key.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Switching to "Work in steps" loses adaptive assistance | fixed | `f71773967` | `tests/test_hint_h2b_review.py::test_f1_*` (6); `PracticeScreen.adaptiveHandoff.test.tsx` "F1: ..." (3) |
| F2 | High | The clickable key bar delivers invisible hints in steps mode | fixed | `f71773967` | `PracticeScreen.adaptiveHandoff.test.tsx` "F2: ..." (4) |
| F3 | Medium | Repeated fallback clicks count the same authored hint twice | fixed | `f71773967` | `PracticeScreen.adaptiveHandoff.test.tsx` "F3: ..." (2) |
| F4 | Medium | Committed feedback can permanently miss learner-text processing | fixed | `f71773967` | `tests/test_hint_h2b_review.py::test_f4_*` (2) |
| F5 | Medium | Interrupted outcome placement is never resumed | fixed | `f71773967` | `tests/test_hint_h2b_review.py::test_f5_*` (4) |
| F6 | Medium | Waypoint success excludes progress established by the next hint | fixed | `f71773967` | `tests/test_hint_h2b_review.py::test_f6_*` |
| F7 | Medium | Surface filtering does not filter chooser statistics or avoidance | fixed | `f71773967` | `tests/test_hint_h2b_review.py::test_f7_*` |

The references were regenerated in `df68dbb34`.

**Reproduction.** The new tests were run against the pre-fix sources: the
`src/` files and the three frontend files were restored from HEAD
(`e02b62c37`) and then put back.

- Backend: 13 failed and 1 passed. The test that passed is
  `test_f1_before_the_fix_the_same_flow_recorded_an_unassisted_attempt`, which
  pins the reproduction: a service hint followed by a workbench submit records
  `hints_used = 0`.
- Frontend: 8 failed and 1 passed. The test that passed is the adaptive-off
  hand-off, which is unchanged by design.

## What changed

### F1: hints carried into steps

The practice screen's `workbench.open` now sends two new optional inputs,
`carriedSubmissionId` and `carriedSessionId`, which name the answer box's
submission. The sidecar (`_link_carried_hints`) then links its own rows to the
problem through `help_assists.link_to_workbench`. A row is linked only if it
was shown, was counted by the server, was taken by no attempt and has no
closed count. The link uses `workbench_session_id`, which already exists and
can be set once (the identity trigger allows NULL to a value). Because the
server links rows it recorded itself, a client cannot inflate the count by
sending a number.

At submit:

- `workbench.submit` passes `workbench_session_id` to `submit_attempt_on`.
- `ServerHintFold` carries the id, and `read_fold` adds `carried_fold` by
  H2a's rule: levels 1-3 count one each, and levels 4-5 set primed.
- The attempt's `BEGIN IMMEDIATE` refold reads the same fold. In that same
  transaction, `attach_carried` attaches the rows to the attempt, after
  `attach_keyless`.

H2a's per-key fold, fence, `mark_shown` and delivery are unchanged.

Counting rules:

- The session view's `carriedHints` stays the client's own count, which the
  answer box restores on the way back.
- The record line names the carried server hints too ("N shown on the answer
  box").
- If the learner goes back and submits on the answer box, the hint counts once,
  under its key. Whichever attempt commits first takes the rows.

Tests cover:

- a next step at level 3 carrying into the workbench submit;
- a service-served authored hint (counts 1, no reveal row) plus a level-5
  walkthrough (primed);
- the client's authored offer added to the server rows, never doubled;
- going back to the answer box, where the hint counts once;
- rows that must not link: another key, another session, or a count closed by
  a later attempt.

### F2: no hint where the panel is hidden

- `revealHint` refuses in steps mode and while the screen is entering steps.
  The key bar's `^h` is a control only outside steps.
- The hook has a new `hold()`. It refuses new requests, waits for requests and
  authored offers in flight, and cancels a job that is still pending. Since
  only a read delivers a job, a job that is never read is never shown. A job
  that answers `already_shown` is read once and kept, so it shows on the
  answer box and stays counted, because it was linked before the problem
  opened.
- Polls stop while held.
- The practice screen awaits `hold()` before calling `workbench.open` (both
  open and resume) and calls `resume()` once the answer box is back.

### F3: one authored offer per click

`takeAuthoredInstead` claims the offer synchronously, once per job, and
disables its control (`offerBusy`) while the cancel answers. It reveals the
authored hint only if the request it was offered for is still the pending one.

### F4: learner texts that were never queued

- A new `sources.hint_feedback_ids` lists the texts.
- `sweep_backlog` (`learnloop gaps run --backlog`) now sweeps `hint_feedback`
  whenever the pipeline and adaptive hints are both on. A new `kinds`
  parameter narrows the sweep. The sweep's result dict gains a
  `hint_feedback` count, and one existing expectation was updated for it.
- A new `reconcile_hint_feedback` runs when the sidecar opens a vault
  (`SidecarContext.reconcile_hint_work`). It is idempotent, reads no text and
  calls no model.

### F5: outcome placements that never ran

- A new `outcome.reconcile_outcome_placements` runs at vault open. It looks
  for hinted attempts that are not fully correct, have an answer, are under
  `RECONCILE_LOOKBACK_DAYS = 14` days old and were never placed. It handles at
  most `RECONCILE_LIMIT = 20` per pass, in one background thread in H1's
  registry. These two constants only bound runaway work; they are not money
  settings.
- Each placement goes through `place_outcome`, so it keeps the same switches,
  claim, lease, fence and maps' envelope. A paid answer checkpointed before
  the interruption is recovered from the checkpoint, with no second call; a
  test interrupts after the checkpoint to show this.
- The pass stops at `capped`, `unpriced`, `unavailable` or `stale`.
- `_cached_submission` (receipt retries, and recovery of a committed attempt)
  now schedules placement too.
- `_hinted` returns False for an attempt that is already placed, so a retry
  starts no thread.

### F6: waypoint goals

`goals_reached_without_more_help` now counts every waypoint whose unaided
progress was reached. That includes progress established by the next hint's
placement, which is §6.1's "before any further help". `unaided()` already
answers `more_help_followed` when the next placement cannot settle it.

### F7: `--surface` filters

- `hint_choice` judgments are filtered to the assist rows of the selection
  (their `left_id`).
- Avoidance reads only the attempts of the surface's entry surfaces
  (`ATTEMPT_SURFACES`):
  - `practice` maps to `desktop_practice`;
  - `workbench` maps to the two workbench surfaces;
  - `guided_redo` and `tutor` are reported as not measured (`null`), since
    they have no attempts of their own yet.
- The receipts stay global and are labelled `receipts_scope: "all_surfaces"`.
- The filter test asserts every section.

## Deviations and notes

- **Notes for the owner.** These are not open questions; nothing here needs a
  decision.
  - A hint delivered in the instant before the learner chose "Work in steps"
    is counted, and it shows once the answer box is back. It is never shown
    in steps. This is the conservative side of G-H3: counted, never
    unrecorded.
  - The start-up placement pass can make up to 20 placement calls per vault
    open. Each is inside the maps' envelope, or on the subscription.
- **Scope.** H2a's fold, fence, delivery and contract code were extended
  rather than reworked. `ServerHintFold` gains one optional field, `read_fold`
  one optional argument, and `apply_attempt` one attach call beside
  `attach_keyless`. H0's attach and H1's validator and lifecycle are
  untouched. No migration, table role or config key was added.
- **Pre-existing failure.** `desktop_validate.py` stops on
  `apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts`,
  which has no desktop classification. That file comes from `b1087be0a` and is
  not part of this stage. The DB references and the vault validator pass.

## Gate (this fix step)

| step | result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 26 kept, 0 broken |
| targeted `uv run pytest -n auto` (108 files, listed below; `TMPDIR=fixtures-local/tmp`) | 2582 passed, 2 xfailed (164.9 s) |
| `uv run pytest -m durability` on the same 108 files | 35 passed |
| `uv run pytest --durable-sqlite tests/test_hint_h2b_review.py` | 14 passed |
| `npm install`, `npm run typecheck` | ok, no errors |
| `npx vitest run` (12 files below) | 145 passed |
| `npm run frontend:build` | built |
| `cargo check` | not needed (nothing under `src-tauri` changed) |
| `db_generate_reference.py`, `db_validate_reference.py` | 0 errors (head 212); `validate_vault.py` and `module_validate.py` pass |

**Test files run.** These are the changed and affected files plus the contract
pins:

- **Pytest (108):** test_ai_compare, test_approach_map_boundaries,
  test_approach_map_replay, test_approach_maps, test_architecture,
  test_assessment_enforcement, test_assumed_known,
  test_concept_animation_service, test_decider_landing,
  test_diagnosis_input_provenance, test_diagnosis_input_provenance_landing,
  test_diagnosis_replay, test_diagnostic_probe_freshness,
  test_embedding_backfill, test_held_grade_composition,
  test_help_assists_schema, test_hint_authored_reveal_ruling, test_hint_blind,
  test_hint_contracts, test_hint_discriminating, test_hint_evidence,
  test_hint_feedback_texts, test_hint_feedback_widening, test_hint_h2a_review,
  test_hint_h2a_review_round2, test_hint_h2a_review_round3,
  test_hint_h2a_review_round4, test_hint_h2b_review, test_hint_kill_switch,
  test_hint_outcome, test_hint_replies, test_hint_report, test_hint_service,
  test_hint_telemetry, test_hypothesis_reference_contract,
  test_ingest_ownership, test_learner_text_gaps,
  test_learner_text_gaps_composition, test_learner_text_gaps_flow,
  test_learner_text_gaps_rereview, test_learner_text_gaps_review,
  test_learner_text_source_widening, test_library_ask,
  test_library_ask_expand, test_library_asks_migration,
  test_mastery_step_attribution, test_mcp_c1a_landing, test_mcp_c1a_narrow,
  test_mcp_c1a_review, test_mcp_tools, test_mobile_allowlist,
  test_mvp016_upgrade, test_placement_opening_probes, test_placement_report,
  test_placement_signals, test_probability_cli, test_probe_pool_empty,
  test_probe_remint, test_quick_check, test_reader_active_reading,
  test_reader_compare_table, test_reader_cues,
  test_reader_find_sources_callers, test_reader_formative_texts,
  test_reader_guidance, test_reader_inquiry_status, test_reader_intent,
  test_reader_intentions, test_reader_observation_records, test_reader_recap,
  test_reader_recap_review, test_reader_recap_review_r2,
  test_reader_reconstruct, test_reader_rw1b_fix_round4,
  test_reader_rw1b_review, test_reader_workbench_rw2a, test_reader_wrap_up,
  test_reading_request_sweep, test_required_method_round3_review,
  test_rw4_kill_switches, test_serve_eligibility, test_sidecar_contract,
  test_source_service_spend_accounting, test_source_service_spend_envelopes,
  test_spend_controls, test_stuck_prompt, test_stuck_prompt_composition,
  test_stuck_prompt_replay, test_t6_followup_composition,
  test_t6_followup_review, test_tier1_decider, test_tutor_promotion_service,
  test_ux_phase1_auto_build, test_ux_phase1_finish,
  test_ux_phase1_review_fixes, test_ux_phase1_round2_rereview,
  test_ux_phase4_landing, test_desktop_rpc_contract,
  test_sidecar_serializer_snapshot, test_table_roles,
  test_coordinated_migrations, test_tracked_fixture_databases,
  test_cli_help_snapshot, test_receipt_exactness,
  test_characterization_probe_submission.
- **Vitest (12):** PracticeScreen.adaptiveHandoff, PracticeScreen.adaptiveHints,
  PracticeScreen.adaptiveOff (the base snapshots, unchanged),
  PracticeScreen.hintTelemetry, PracticeScreen.phase4, PracticeScreen,
  PracticeScreen.workbench, practice/HelpStyleSettings, practice/hintCopy,
  workbench/stepModel, workbench/switchOff, workbench/Workbench.

The full suite, the whole durability lane and the whole vitest run are left
to the landing gate (owner rule, 2026-10-17).

## Re-review

Codex re-reviewed `e02b62c37..hints/h2b` (job `20261018-105207-cFaDI3`) and
reopened F1 and F2 (High). It also found F8 and F9 (Medium). This round
reproduced each finding with a test that failed before the fix, then fixed
it. All four are fixed and none was rejected. No live or paid model call was
made; every model-backed path is tested with fakes. There is no migration, no
new config key and no new RPC.

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Reopened: a second "Work in steps" after closing the problem loses the carried hints | fixed | see the commit recording this section | `tests/test_hint_h2b_rereview.py::test_f1_*` (5) |
| F2 | High | Reopened: `hold()` does not wait for polls in flight and resolves when the cancel fails | fixed | same | `practice/useAdaptiveHints.hold.test.tsx` (3); `PracticeScreen.adaptiveHandoff.test.tsx` "F2 (re-review): ..." |
| F8 | Medium | The vault-open placement pass can starve placeable attempts | fixed | same | `tests/test_hint_h2b_rereview.py::test_f8_*` (2) |
| F9 | Medium | Carried hints lose their submission timing | fixed | same | `tests/test_hint_h2b_rereview.py::test_f9_*` (2) |

**Reproduction.** The new tests were run on the unfixed tree (`9193ce661`)
before any source change:

- Backend: 6 failed and 3 passed. The two F1 reproductions (close, open a new
  problem, submit: `hints_used = 0`, and a level 5 that no longer primes), both
  F9 tests (`submitted_at` stays NULL; the store function did not exist) and
  both F8 tests failed. The 3 that passed are guards for the fix, not
  reproductions. They check that the hints count once, that a reopened problem
  keeps its own hints, and that nothing crosses practice sessions.
- Frontend: all 4 new tests failed. `hold()` resolved while the read was still
  answering. It also resolved (with no value) when the cancel failed. The
  screen then opened the workbench anyway.

### F1: hints carried into a closed problem

The link from a hint row to its problem (`workbench_session_id`) can be set
only once, because H0's identity trigger allows NULL to a value and nothing
else. So a second hand-off cannot link again the rows the closed problem
holds. Changing the trigger would need a migration that rewrites H0's
schema, which this stage rules out (migration 212 only widens the
`hint_feedback` source kind).

The fix leaves the link alone. Instead, a problem the learner closed
(`abandoned`) *releases* the rows it carries. `help_assists._carried_rows`
gives one definition for the fold, its attach and its stamp. A workbench
problem carries:

- the rows linked to it, as before;
- the rows linked to a closed problem on the same item, in the submit's
  practice session. These are the rows the answer box's own key would still
  count there.

Before Submit, the record line counts released rows from any practice
session still open.

Released rows count once, whichever attempt commits first:

- the problem opened in place of the closed one;
- the closed problem itself, if it is reopened;
- the answer box, under its key.

They never cross into another practice session, so a problem in a later
session does not inherit an old hint. Like rows linked directly, released
rows attach to the attempt in the attempt's own write transaction. H2a's fold,
fence, `mark_shown` and delivery are unchanged. `read_fold` and
`attach_carried` now pass the practice session they already held.

### F2: a hold that waits for reads, and fails when it must

In `useAdaptiveHints`:

- A poll's `practice.hint_job` read is now tracked with the requests and
  offers in flight, so `hold()` waits for it.
- A read that delivers a hint is shown even if something settled the request
  meanwhile. Entries are de-duplicated by `assistId`. Before, the read was
  dropped because `pendingRef` had been cleared.
- A poll that errors while held leaves the job to `hold()`.
- `hold()` now resolves to a boolean.
  - It resolves `true` when nothing is pending: the hint was cancelled, or it
    was delivered and read.
  - It resolves `false` when the cancel or the read after `already_shown`
    fails. In that case the request stays pending, holding ends, and a new
    poll chain starts. A chain token stops the old chain, so there is never
    more than one chain.
- When the hold fails, `PracticeScreen` keeps the answer box and does not
  call `workbench.open`. The hint is delivered on the answer box, where the
  learner can see it, and the error is reported once.

### F8: page past what cannot be placed

`reconcile_outcome_placements` used to read one page of 20 candidates. It now
reads pages of `RECONCILE_PAGE = 50`, oldest first, with a
`(created_at, id)` cursor. It moves past candidates that place nothing and
spend nothing (`not_due`, `no_map`, `already_placed`, `busy`, `disabled`).
`RECONCILE_LIMIT = 20` now counts placements, not candidates.

Other behaviour:

- The pass stops at `capped`, `unpriced`, `unavailable` or `stale`, as before.
- One pass runs per vault at a time, guarded by an in-flight key.
- Each candidate is claimed in memory only while it is being placed, so a
  submit's own placement is not doubled.

`RECONCILE_PAGE` is a module constant that bounds a read, not a setting, so
it does not go in the config or the parameter registry. `RECONCILE_LIMIT` is
handled the same way.

### F9: carried rows' submit time

`help_assists.stamp_carried_submitted`, called through
`telemetry.stamp_carried_submission` from `submit_attempt_on` and
`submit_dont_know_on` right after the keyed stamp, writes the workbench
submission's admission time on the rows it carries. The rule is the same as
`stamp_submitted`: the first stamp stays, and the stamp is made only when
the keyed stamp was (telemetry on, with a key).

No latency is written. The workbench's open-to-submit latency is measured
from when the problem opened (`Workbench.tsx` `openedAt`), which is after the
hint was shown on the answer box. Taking away the reveal-to-submit gap would
not give the time from the answer box's open to the hint; it would give a
negative number clamped to 0. So these rows are now timed for "reveal to
submit", and "seconds into the attempt" is reported as `no_submit_latency`
instead of a wrong figure. The test checks both report fields.

### Gate (re-review fix step)

| step | result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 26 kept, 0 broken |
| targeted `uv run pytest -n auto` (contract pins and hint and workbench files, list A; `TMPDIR=fixtures-local/tmp`) | 868 passed |
| targeted `uv run pytest -n auto` (practice and workbench handler callers, list B) | 135 passed |
| `uv run pytest --durable-sqlite` on test_hint_h2b_rereview, test_hint_h2b_review, test_help_assists_schema | 33 passed (the new file 3 more times alone: 9 passed each) |
| `uv run pytest -m durability` on test_help_assists_schema, test_hint_feedback_widening, test_coordinated_migrations | 4 passed |
| `npm run typecheck` | no errors |
| `npx vitest run` (10 files, list C) | 103 passed (78 + 25) |
| `npm run frontend:build` | built |
| `cargo check` | not needed (nothing under `src-tauri` changed) |
| `db_validate_reference.py` | 0 errors (head 212; no schema change); `validate_vault.py` passes |

Two validators fail for reasons outside this step:

- `desktop_validate.py` still stops on `syntheticBook.ts`, as in the first
  round.
- `module_validate.py` reports 844 issues, nearly all missing notes for
  modules this stage did not touch (`learnloop/ai/agreement`,
  `chatgpt_plan/*`, ...). Coverage is 474 of 886 modules.

The first round's record says `module_validate.py` passes, but the
validator's checks are repo-wide and this step adds no module.

**Test files run.**

- **A (pytest):** test_hint_authored_reveal_ruling, test_hint_blind,
  test_hint_contracts, test_hint_discriminating, test_hint_evidence,
  test_hint_feedback_texts, test_hint_feedback_widening, test_hint_h2a_review,
  test_hint_h2a_review_round2, test_hint_h2a_review_round3,
  test_hint_h2a_review_round4, test_hint_h2b_review, test_hint_h2b_rereview,
  test_hint_kill_switch, test_hint_outcome, test_hint_replies,
  test_hint_report, test_hint_service, test_hint_telemetry,
  test_approach_map_replay, test_approach_maps, test_architecture,
  test_help_assists_schema, test_library_asks_migration,
  test_mobile_allowlist, test_reader_workbench_rw2a,
  test_desktop_rpc_contract, test_sidecar_contract, test_cli_help_snapshot,
  test_table_roles, test_coordinated_migrations,
  test_tracked_fixture_databases, test_learner_text_gaps_flow.
- **B (pytest):** test_daily_plan_composition,
  test_daily_plan_review_regressions, test_daily_plan_rpc,
  test_learner_text_source_widening, test_reader_active_reading,
  test_router_r1_composition, test_rw4_kill_switches,
  test_sidecar_item_authoring, test_stuck_prompt,
  test_characterization_probe_submission.
- **C (vitest):** practice/useAdaptiveHints.hold (new),
  PracticeScreen.adaptiveHandoff, PracticeScreen.adaptiveHints,
  PracticeScreen.adaptiveOff, PracticeScreen.hintTelemetry,
  PracticeScreen.phase4, PracticeScreen.workbench, PracticeScreen,
  practice/HelpStyleSettings, practice/hintCopy.

The full suite, the whole durability lane and the whole vitest run are left
to the landing gate (owner rule, 2026-10-17).
