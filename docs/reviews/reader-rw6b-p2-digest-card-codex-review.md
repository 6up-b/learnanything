# Reader RW6b part 2: Codex review fix round (`reader/rw6b-p2-digest-card`)

The review is Codex job `20261101-015047-LptVXa` (gpt-6.1-sol). It reviewed `a53f72a398` and found eight defects: one
High and seven Medium. All eight reproduced. All eight are fixed, each with a test written first. The tests failed
against `a53f72a398`'s code; this was checked by putting the previous source back over the new tests (see the
fail-first notes). One part of F1's suggested fix is declined, with the reason below.

**Spend: $0.** Fakes only. No model, paid or live call. No owner vault, `~/learnloop-vaults`, `~/learnloop-retired`
or `~/learnloop-books` was opened. The reference scripts ran under `env -i` with empty, existing `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, with `TMPDIR` outside the worktree.

**Still no migration, no successor and no new config key.** C1 keeps mvp-0.40. The fix uses part 1's columns, the
existing `judgment_work_claims` table and the existing `digest.*` switches.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Reader activity never reaches the live router | **fixed**; successor part declined | `e1177a2cec` | `test_router_reader_activity.py`: `test_the_section_is_in_the_typed_card_its_text_and_its_hash`, `test_the_router_reads_the_section_and_the_kill_switch_restores_the_predecessor`, `test_the_plan_stores_the_card_with_its_reader_section`, `test_nothing_to_say_leaves_the_predecessor_card_byte_for_byte`, `test_the_card_copy_is_bounded_and_says_what_it_left_out`, `test_an_unreadable_section_is_named_in_the_unknowns` |
| F2 | Medium | Disabling follow-ups also disables new narratives | **fixed** | `fe0ac0f01b` | `test_reader_digest_narrative.py`: `test_with_follow_ups_off_an_ended_session_is_summarized_and_narrated`, `test_below_the_follow_ups_successor_the_summary_row_says_so`, `test_no_summary_row_with_narration_off_or_follow_ups_live[2]`, `test_the_queue_build_narrates_a_session_with_follow_ups_off` |
| F3 | Medium | Concurrent sidecars can pay twice for one narrative | **fixed** | `fe0ac0f01b` | `test_overlapping_narrations_from_two_repositories_pay_once` (a blocking fake holds the first call open while a second `Repository` on the same database narrates) |
| F4 | Medium | The narrative kill switch leaves saved narratives in the card payload | **fixed** | `e1177a2cec` | `test_narration_switched_off_after_a_narrative_was_saved_shows_it_nowhere` (the activity, the card's copy, the built card's text and payload, and the recap/Wrap up view) |
| F5 | Medium | `as_of` does not bound mutable reader state | **fixed** (two inputs stated as current; see below) | `e1177a2cec` | `test_a_historical_cutoff_reads_the_same_after_a_later_resolution`, `..._after_a_later_undo`, `..._ignores_a_later_unaided_success`, `test_a_narrative_written_after_the_cutoff_is_not_shown_at_it` |
| F6 | Medium | Actual missed predictions are always filtered out | **fixed** | `e1177a2cec` | `test_a_real_missed_prediction_reaches_the_section_through_its_figure` (stored `interactive_figures` + `figure_predictions` rows, so the summary carries the production record with empty facets and spans) |
| F7 | Medium | A pending narrative never lands in an already-open recap | **fixed** | `aa99e79156` | `apps/learnloop-tauri/src/screens/reader/narrativeLanding.test.tsx` (3 tests: the card, an open Wrap up, a changed source) |
| F8 | Medium | "Open hypotheses" includes closed and reversed hypotheses indefinitely | **fixed** | `e1177a2cec` | `test_a_reversed_gap_and_a_closed_episode_are_not_open_hypotheses` |

`fdb0f8ac98` has the config, template and registry wording for F1 and F2, and the regenerated DB/config reference.

### F1: the card's "Reader activity" section

- **What was wrong.** Router R2 (R2a's typed evidence registry, R2b + R2c's mixture) is live at `router.mode =
  "mixture"`, the default. The spec's "before R2" clause (§9.2) therefore no longer applied, and nothing rendered the
  section.
- **The fix.**
  - `daily_plan.router_card` puts `router_reader.for_card(activity)` into the card's `evidence_sections.reader_activity`.
    This is R2a's registry hook, used the way R2c used it for teach-back summaries.
  - `router.card.render_text` renders it as `# Reader activity (from the Reader; routing only, never evidence)`. Each
    entry is written as plain words: open questions (the learner's excerpt, or "words withheld (exam_material)"),
    assisted-only work, pending checks with their valuation, missed predictions, open hypotheses, formative records,
    kept comparisons, possible next actions with where each came from, and the narrative with its label and how many
    events it cites.
  - So the section is typed, hashed, stored with the decision (`router_decision_payloads`), and read by both router
    models.
  - `evidence_from_card` never cites it: it is routing only, never evidence (W1). The test pins this.
- **Bounded.** Each list in the card's copy keeps `CARD_LIST_LIMIT = 6` entries and states how many it left out.
  - The kept entries are the newest, or the first in order for follow-ups and next actions.
  - The limit is a prompt-size bound, marked `keep`, the same as R2c's `CARD_LIMIT`. It is not a config key, and the
    module is not in `MODULE_INVENTORY`.
  - `reader_activity_for_card` itself still returns everything.
  - The card's copy leaves out `as_of`, because the card has its own decision time.
- **Predecessor parity.** With `digest.enabled` off (the existing kill switch), or with nothing on the candidates'
  LOs, the card is the predecessor's byte for byte: payload, hash and text. The card's version label does not move
  (R2a: a registry section "without changing this card's version scheme").
- **Unreadable section.** If the section cannot be read, the card's unknowns name it ("reader activity could not be
  read"), following the registry's rule. Before this fix it was only logged.
- **The data fields are gone.** `CardInputs.reader_activity` and `LearnerStateCard.reader_activity` (the unhashed
  side channel) are removed.
- **Declined: "an algorithm successor".**
  - The change is a router-model input, the same class as TE0's confidence events (`docs/reviews/teacher-te0-confidence-events.md`
    §3, ruled no successor against `docs/algorithm-change-playbook.md`).
  - Eligibility, priming and the feasible set are computed before the card is built.
  - The mixture's sampling, its logged propensity and the rule's choices read the candidates, not the card.
  - `router_retrieval.context_text` does not read `evidence_sections`.
  - Replay and rebuild never read the card.
  - The spec says "Successor: None" for RW6 (§9.6). The kill switch with predecessor parity is what the review asked
    for, and it is there.
  - The owner may still rule for a successor at the checkpoint.
- **Also fixed while here.** A named gap's own `kind` (prerequisite, misconception...) used to overwrite the entry's
  `"named_gap"` kind. It is now `gap_kind`.

### F2: narration without follow-ups

- **The fix.** With `digest.narrative_enabled` on and follow-ups not live (`followups.enabled` off, or the vault below
  mvp-0.39), `reader_digest.summarize_ended_sessions` persists each ended session's typed summary as a
  **summary-only digest row**, and narration proceeds from it.
  - The row is `status = 'incomplete'`, with no commitments and no valuation.
  - `valuation_json.not_planned` says why: `followups_off` or `below_followups_successor`.
- **The lifecycle.**
  - *Not planned* is `incomplete` with `not_planned`.
  - *Planned with no checks* is part 1's `planned` row with an empty `chosen`.
  - When follow-ups go live, part 1 plans a summary-only row like any unfinished session. Its narrative stays, because
    `without_narrative` keeps a narrative from superseding a plan.
- **Bounds and gates.**
  - The same time window as part 1 applies (`followups.max_wait_days`), so switching narration on never narrates
    old history.
  - Rows are written only in the background job, and only when a narration could run now (admission). With
    `LEARNLOOP_DIGEST_MODELS=off`, or with no route, nothing is written. This is part 1 exactly.
  - No migration was needed: `incomplete` is an existing status, and nothing user-facing reads it.
  - The sidecar's `prepare_followups` starts the job for these sessions too.

### F3: one paid call per session across processes

- **The claim.** `narrate_digest` takes the session's durable claim in `judgment_work_claims` (task
  `reader_digest_narrative`, key `reader_digest_narrative:<digest_id>`) before anything is asked.
  - It reuses the lease, heartbeat and release of the approach-map builds, the same way AD and H2b do
    (`hints.map_builder._claimed`).
  - It does not wait: a held claim returns the new status `claimed`, with no call.
  - The holder re-reads the row before asking.
  - A dead holder's lease lapses within 120 s, and the next Today build retries.
- **Publication** stays the conditional write (`prompt_version IS NULL`). A writer whose lease lapsed mid-call still
  records what it paid for, so that call is never paid again, and it never overwrites another writer's narrative. The
  old "two writers race" test (two sequential setter calls) is kept as the setter's own test. The new test exercises
  admission across two repositories with the call in flight.

### F5: what `as_of` bounds, and what it cannot

- **Now read before `as_of`:**
  - digest rows, by creation and end;
  - an inquiry's status, from its `inquiry_status_set` events. Before the first event, the status is that event's
    previous status. With no event at all, it is the current status;
  - a follow-up's disposition and due date, from its commitment events and versions. `resolve_disposition` gains a
    `before=` keyword (the default is unchanged), and a commitment created after the cutoff is left out;
  - a claim's answer, from its facet curve's points;
  - a gap's reversal and a probe episode's close (`completed_at`, else `updated_at`);
  - the narrative, from its `judgment_ledger` verdict's time.
- **Read as they are now, because no history is kept** (stated in the module docstring):
  - a rival's facet marginal (`facet_uncertainty_state`);
  - a causal factor's pending decision;
  - a digest row's summary rewritten by a later re-plan of the same session.

  These entries stay listed with their source rows. Historical cutoffs are not read by any path today, because the
  card is built at the decision's own time.

### F6, F8

- **F6.** A prediction record's scope comes from its figure's passages: `figure_predictions.figure_id` →
  `interactive_figures.span_ids_json` (else `input_span_ids_json`) → `learning_objects_for_span`.
- **F8.** Open hypotheses are now resolved as of the cutoff:
  - a reversed named gap is left out (the card's own open problems keep it, with its reversal);
  - a rival lists only the targets still open: a probe episode closed by then, or a gap reversed by then, is settled;
  - a rival with none left goes;
  - each gap and rival question appears once, from the latest session that named it, with its source rows.

### F7: the pending narrative lands in place

While the card shows the narrative as "writing a summary", `useReaderRecap` re-reads the surface showing it every
`NARRATIVE_POLL_MS` (10 s), and the same applies to an open Wrap up.

- It re-reads only the surface or surfaces that are waiting.
- It stops when the narrative lands or stops waiting.
- The timer is cleared when the source changes, the card is dismissed, Wrap up closes, or the Reader unmounts.
- A failed read schedules the next one.
- The interval is a UI refresh guardrail, marked `keep`.
- Nothing takes focus or animates.

## Fail-first

- Each Python fix was checked by putting `HEAD`'s version of the changed modules back
  (`git show HEAD:<path> > <path>`, then restoring the new version from a scratch copy; no `git stash`).
- `router_reader.py`, `router_card.py`, `router/card.py`, `commitments.py`: 13 of the 20 tests in
  `test_router_reader_activity.py` failed (every new one). The 7 that still passed are part 1's.
- `reader_digest.py`, `handlers/reader_followups.py`: the 6 new tests in `test_reader_digest_narrative.py` failed,
  and the 23 existing ones passed.
- `useReaderRecap.ts` (with only the constant exported): 2 of the 3 tests in `narrativeLanding.test.tsx` failed (the
  card and Wrap up landings). The third test checks the cleanup and passes either way.

## Gate (this step; the full suite runs once in the landing gate)

Every pytest, vitest, npm and cargo command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`.

- pytest ran at `-n 6`, and vitest at `--maxWorkers=4`.
- The 192-file run was serialized behind `flock /tmp/learnloop-fullsuite.lock`.
- `TMPDIR` was outside the worktree.
- One test run at a time.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **36 kept, 0 broken** |
| `pytest -n 6 tests/test_router_reader_activity.py` (during the fix) | 20 passed |
| `pytest -n 6 tests/test_reader_digest_narrative.py` (during the fix) | 29 passed |
| `pytest -n 6` over 192 files (list below), behind the flock | **3333 passed, 19 skipped, 3 xfailed** (32 min 49 s) |
| `pytest -n 6` over `test_router_reader_activity.py`, `test_reader_digest_narrative.py`, `test_router_card.py`, `test_architecture.py` (rerun after line-wrap-only edits made while the 192-file run was in flight) | 77 passed |
| `npm install`, `npm run typecheck` | ok (no errors) |
| `npx vitest run --maxWorkers=4` over 9 files (list below) | **46 passed** (9 files) |
| `npm run frontend:build` | built (the usual chunk-size warning only) |
| `db_generate_reference.py`, then `db_validate_reference.py` (under `env -i`) | regenerated; `"errors": []`. The schema is unchanged; only the config docstrings' text and line numbers moved |

**The 192 files of the targeted pytest run** are:

- the stage gate's 169 files, which are listed in `docs/reviews/reader-rw6b-p2-digest-card.md`;
- 23 files that exercise `curriculum.commitments` (`resolve_disposition` gained `before=`): `test_commitment_arcs.py`,
  `test_commitments.py`, `test_controller_ownership.py`, `test_cross_seam_exposure.py`,
  `test_daily_loop_reference_adoption.py`, `test_deliverable_path.py`, `test_depth_transition.py`,
  `test_dl2_rw4b_keyed_pick_check.py`, `test_dual_authority_administration.py`, `test_golden_path_assessment.py`,
  `test_intent_exclusion.py`, `test_intent_fix_round4.py`, `test_intent_goal_deadline.py`, `test_intent_resolution.py`,
  `test_journey6.py`, `test_reader_adoption_ownership.py`, `test_reader_authoring.py`, `test_reader_ca1_as_printed.py`,
  `test_reader_reconstruct.py`, `test_reader_rw1b_fix_round4.py`, `test_reader_rw1b_review.py`,
  `test_staged_policy.py`, `test_state_signals.py`.

The 169 cover the two changed test files, every `test_router_*.py`, the card builder, the reader follow-ups, digests,
recap and Wrap up, and the contracts: the config defaults snapshot, CLI help snapshot, serializer snapshot, desktop RPC
contract, mobile allowlist, architecture, table roles, coordinated migrations and tracked fixture databases.

**The vitest files:** `screens/reader/narrativeLanding.test.tsx` (new), `DigestNarrative.test.tsx`, `RecapCard.test.tsx`,
`WrapUp.test.tsx`, `recapReview.test.tsx`, `recapSwitchOff.test.tsx`, `screens/ReaderScreen.recap.test.tsx`,
`ReaderScreen.recapReview.test.tsx`, `ReaderScreen.parity.test.tsx`. Together these exercise `useReaderRecap` and the
narrative's surfaces.

Not run here:

- **cargo check:** nothing under `src-tauri` changed.
- **The durability lane:** no migration and no DB or connection code changed. The claim reuses
  `judgment_work_claims` through existing code.
- **The desktop catalog:** it was already stale before this round (`DigestNarrative.md` is missing since part 2's
  first pass). It is regenerated at landing (`desktop_generate.py`), as the queue notes say.

## Open items for the owner

1. **F1's successor.** The card's Reader activity section now reaches the router models under `digest.enabled`, with
   no successor, following TE0's ruling. If you want it behind a successor instead, it would be mvp-0.41 after C1's
   mvp-0.40.
2. **Inputs with no history** (F5): a facet marginal, a causal factor's pending decision, and a re-planned digest
   row's summary are read as they are now at a past `as_of`. A historical card replay would need their history.
3. **The original record's open questions 2–4** (narratives need part 1's row; the card section not rendered; the
   narrative's time) are closed by F2, F1 and F5.
