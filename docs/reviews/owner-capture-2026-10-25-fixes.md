# Owner capture 2026-10-25: four behaviour fixes

Branch `fix/owner-capture-1025` from `main` at `fa2eb72f8`. The owner hit these
on 2026-10-25 in the desktop app (simple shell) on the probability vault:

- 11:00 "learnloop ask needs a ux overhaul and should reset hints if the question is reattempted instead of reusing the same hints/questions that were asked last time this question was served."
- 11:01 "learnloop ask doesnt work in Work in Steps mode when doing a question"
- 11:39 "choosing guide/balanced/struggle didn't change anything for question in probability vault that already had hints. also submitting answer didnt show grader screen. got error 'the scheduler offer does not belong to this item/session or was already consumed'."

This stage fixes behaviour only. The Ask UX overhaul is a separate design item
and is not part of it. Citations of the root causes are to `fa2eb72f8`.

## The chain the owner hit (B3 and B4 have one root cause)

These three notes describe one session. The owner opened a question that
already had hints (an item with authored hints), revealed a hint, and moved to
"Work in steps". Ask did nothing there (B1). They submitted in steps. The
practice screen's draft of the answer box stayed behind: its retry key, its
hint count and its binding to the queue's offer. When the item came back,
App restored that draft, and two things followed. The earlier hints showed as
if they belonged to this attempt, and the earlier Ask questions showed too
(B3). The submit then went out under the old key, whose offer the steps
attempt had already answered, and failed (B4). Separately, the help style
had no effect because no Decider is routed in the owner's vault (B2).

I reproduced B4 end to end, with the in-process sidecar handlers, on a
backup-API copy of the owner's vault (`/home/saturn/learnloop-backups/s0/probability`
copied to `fixtures-local/capture-1025-base` and `-fix`). The run used
`env -i` with an empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR,
`LEARNLOOP_HINT_MODELS=off`, every provider `base_url` set to
`http://127.0.0.1:9`, and a fake grader. The item was
`pi_exercise_01kyn2kdf7h2kba1fp7wv7t3w5`, which has 4 authored hints.

| | `fa2eb72f8` | this branch |
|---|---|---|
| checkpoint after the steps submit | still the item, `{hintsUsed: 1, submissionId: box-key}` | cleared |
| the answer box's key submitted again | `SidecarError: The scheduler offer does not belong to this item/session or was already consumed.` | graded under `box-key~after~<steps attempt>`, unattributed |
| model call receipts | none | none |

## B1: Ask did not work in "Work in steps"

**Root cause.** In steps mode the practice screen hides the whole answer-box
action row, and the Ask button lives in that row
(`apps/learnloop-tauri/src/screens/PracticeScreen.tsx:2007`). Its key
handler also returns at once in steps mode, so `?` did nothing
(`PracticeScreen.tsx:850`). The workbench had no Ask of its own. The only way
in was the command palette, and that path sent nothing about the steps.

**Fix.**
- `Workbench` takes `onAsk`, which gives it an "ask · ?" action and the `?`
  key when the learner is not typing. It also takes `onWorkChange`, which
  reports the live steps (numbered, with stuck steps marked) as they change.
  `stepsAsWork` is the formatter.
- The practice screen passes both. Its Ask, its `?` (handled when no element
  has focus) and the command palette's Ask (through `onAskState`) carry the
  steps as `workMd`, with `attemptProgress` taken from the steps.
- `AskOverlay` sends `workMd` as `learnerDraftMd` with every practice
  question asked from steps. The sidecar already accepts that field. On the
  answer box nothing changes: the draft still goes only with "Explain this
  with my work". The Reader's workbench passes no `onAsk`, so it keeps its
  own Ask.

**Tests (fail on `fa2eb72f8`):**
- `src/screens/PracticeScreen.ownerCapture1025.test.tsx`: the Ask button in steps, the `?` key, the palette's state.
- `src/screens/workbench/ownerCapture1025.test.tsx`: the workbench reports its steps and offers Ask.
- `src/components/AskOverlay.steps.test.tsx`: `learnerDraftMd` from steps.

Two guard tests pass on both commits: no Ask button without `onAsk`, and the
answer-box draft is not sent with an ordinary question.

## B2: the help style did not change the next hint

**Root cause.** The help style was read only by the Decider (`hint_chooser`).
The owner's vault routes no Decider, so every Hint press took the fallback.
That fallback serves the item's authored hints in order, then the next step,
and never reads the style (`src/learnloop/hints/chooser.py:237`). On an item
with authored hints, every style therefore served the same hints. The
workbench had the same problem in two places:
- Its fallback suggestion was the Reader's fixed progression (`src/learnloop/hints/workbench.py:638`).
- A Decider suggestion made under one style was reused after the learner
  changed the style. Taking the suggested rung served the old draw
  (`src/learnloop/hints/service.py:831`), and the open ladder never asked
  again (`useWorkbenchHelp.ts:403`).

There is no cache of written hints. The only reuse of a hint decision across
styles was this suggestion.

**Fix.**
- **Practice fallback** (`fallback_choice`, "More" presses only; replies and
  levels the learner took keep their rules):
  - *balanced* is §4.5's order, unchanged.
  - *let me struggle* serves one level above the highest level shown in this
    attempt, starting at level 1 (an approach question, then "where it stops
    holding"). From level 3 it follows the balanced order, so "More" still
    goes up.
  - *guide me* serves the next step written for the learner's work before
    the item's general hints.
- **Workbench fallback suggestion** (`styled_level`):
  - *balanced* is D8 exactly.
  - *struggle* never suggests worked help. Rungs 4 and 5 can still be taken.
  - *guide me* starts at rung 3.
- **Stale suggestions.** The chooser's `hint_choice` rationale now records
  `help_style`. A suggestion whose recorded style differs from the current one
  is not reused: the rung is drawn again under the new style. Rows written
  before this change have no recorded style and are reused as before. In the
  UI, changing the style with the ladder open asks for a new suggestion.
- **Recording.** Each service row records the style it was chosen under, in
  `contract_failures_json.state_at_request.help_style`.

**Tests (fail on `fa2eb72f8`):** in `tests/test_owner_capture_1025.py`:
- `test_b2_the_help_style_changes_the_first_hint_the_fallback_serves` (3 styles). The balanced case serves what it always served; on the old code it fails only on the recorded style.
- `test_b2_let_me_struggle_still_goes_up`
- `test_b2_the_workbench_fallback_suggestion_reads_the_style`
- `test_b2_a_suggestion_judged_under_another_style_is_not_reused`

In vitest, `src/screens/workbench/ownerCapture1025.test.tsx` checks that the
open ladder asks for a new suggestion on a style change. A guard test checks
that a closed ladder asks for nothing.

**What the owner should know.**
- With no Decider routed, the style now changes which hint comes first. Each
  hint is still counted the same way: levels 1-3 add one to `hints_used`.
- When the hint writer cannot run (plan down, capped, models off), only the
  item's authored hints can be served, whatever the style. That path is
  unchanged.
- Under *struggle* and *guide me*, a written hint can now replace an authored
  one. A written hint that overlaps the answer key writes its `tutor_answer`
  reveal row, as it already did on the Decider path. Authored hints write
  none.
- Balanced, the default, serves exactly what it served before.
- The fallback's order now depends on the style. The style is recorded, so
  a draw stays reproducible from its row (propensity 1, as before). This
  deviates from adaptive-hints D3 and Reader D8, which fix the fallback's
  order. The specs should note it.

## B3: a reattempt reused the earlier hints and Ask questions

**Root cause, hints.** A steps submit left the answer box's draft in the
session checkpoint and in App's local mirror. The sidecar did not clear it
(`src/learnloop_sidecar/handlers/workbench.py:1096` marks the problem
submitted and stops there). The practice screen did not acknowledge it
either: `onSubmitted` went straight to feedback (`PracticeScreen.tsx:1767`),
and the unmount flush saved the draft again (`PracticeScreen.tsx:649`). The
next serving of the item restored the old retry key and the old hint count
(`app/practiceDraft.ts:55`, `:76`), so the earlier hints were shown as this
attempt's.

**Root cause, Ask.** The practice transcript, the turns given to the tutor
and the practice question budget were all keyed by (item, session) for the
whole session. Every serving of the item in a session therefore shared one
thread (`src/learnloop_sidecar/handlers/tutor_qa.py:547`,
`src/learnloop/tutor/tutor_qa.py:291`, `:1506`).

**Fix.**
- **Server.** The workbench submit clears its item's practice checkpoint in
  its practice session (`_close_answer_box_draft`). It uses
  `clear_practice_checkpoint_for_item`, so another item's draft is left
  alone.
- **Client.** After a steps submit, the practice screen stops the unmount
  flush and clears App's mirror of the answer box's draft (key and item). The
  next serving then gets a fresh key, a fresh service hint ladder (rows are
  read by key) and no restored hint count.
- **Ask.** `practice_thread_events` defines the thread as the practice
  questions on (item, session) asked since the item's last attempt. That is
  the window a question is counted in as a hint
  (`hint_equivalents_for_submission`). The transcript, the turns sent to the
  tutor and the budget all use it.

**Tests (fail on `fa2eb72f8`):**
- `tests/test_owner_capture_1025.py::test_b4_a_steps_submit_closes_the_answer_boxs_draft`
- `tests/test_owner_capture_1025.py::test_b3_a_reattempt_starts_a_fresh_ask_thread`
- the vitest "B3/B4: a steps submit supersedes the answer box's draft"

**Evidence is unchanged.**
- No row is deleted. `help_assists` and `question_events` keep every earlier
  hint and question, and the feedback and history views still show them.
- The hint-equivalence window was already per attempt, and the B3 test
  checks that a question asked on attempt N is not counted on attempt N+1.
- After a steps submit, the stale client hint count can no longer reach the
  next attempt. Before this change it could: the restored `hintsUsed` was
  sent as that attempt's own count. That was the one evidence error in the
  chain.
- Change to know about: the practice budget (`tutor_qa.max_questions_practice`,
  3) now applies per attempt, not per (item, session). A learner who
  reattempts an item in one session can ask 3 more questions.

## B4: "The scheduler offer does not belong to this item/session or was already consumed."

**Root cause.**
- The answer box's draft binds its retry key to the queue's offer
  (`submission_intents`, immutable).
- The steps submit names the same offer and is graded first, so that
  attempt takes the offer.
- When the item came back, App restored the old key, so the screen sent no
  offer (`app/practiceOffer.ts:41`). The bind returned the key's original
  offer (`src/learnloop/db/stores/collection.py:141`), and the attempt's link
  refused it because another attempt had answered it
  (`src/learnloop/db/repositories.py:18724`).
- A screen still holding an answered offer under a new key failed earlier,
  at `collection.py:131`. That failure also broke draft saves.
- Either way the submit raised `validation_error`: no grade and no feedback
  screen. The answer stayed only in the draft.

**Fix (root cause).** This is B3's fix: a steps submit supersedes the answer
box's draft, so the old key is never reused.

**Fix (fail soft, `src/learnloop_sidecar/handlers/practice.py`).**
- `_bind_offer`: an offer of this item in this session that another attempt
  already answered is dropped, with log event `scheduler_offer_stale`, and
  the attempt is unattributed. This matches the workbench's kept offer
  (review F13).
- Foreign offers are still refused: another item's or session's offer, or an
  id that is not an offer. `test_sidecar_contract` and the teach-back tests
  pin that.
- `answering_key`: a retry key whose bound offer another submission's
  attempt answered is written under the successor key
  `<key>~after~<that attempt>`. The key is deterministic, so a retry or a
  `recover_practice_submission` finds the same attempt. The new attempt is
  never read as a second answer to the same serve, because the old key's
  intent cannot be changed. Its server hints fold by the keyless window (the
  item's last attempt in this session, H2b ruling R1), so the earlier
  attempt's hints are not counted again. `submit_attempt`, `submit_dont_know`
  and `recover_practice_submission` all use it.
- New read-only repository methods: `scheduler_offer_answered` and
  `submission_offer_answered_elsewhere`.

**Tests (fail on `fa2eb72f8`):** in `tests/test_owner_capture_1025.py`:
- `test_b4_a_steps_submit_closes_the_answer_boxs_draft`
- `test_b4_a_submit_under_a_key_whose_offer_another_attempt_answered_still_grades`: graded, unattributed, the offer keeps its one attempt, and a retry returns the same attempt.
- `test_b4_a_submit_naming_an_answered_offer_still_grades`

**Persisted meaning.** Scoring, scheduling, serving and propensities do not
change, so no successor is needed under the algorithm-change playbook. A
submit that used to fail now records an attempt with no scheduler
attribution. That is the existing "direct selection, never inferred" case: no
propensity is claimed for a serve the attempt did not answer, and the
answered offer keeps exactly one attempt. The successor key appears in
`practice_attempts.submission_id` and `submission_intents`.

## Gate

| Check | Result |
|---|---|
| Targeted pytest (`-n 6`, 5G scope): the new file; hint, workbench, Reader RW2 and RW2a; tutor and question; collection, sidecar contract, daily plan, teach-back, router; AD guard and contract; architecture; mobile allowlist; sqlite copies; field signals | all pass |
| Durability lane (`--durable-sqlite`): the new file, collection, sidecar contract, daily-plan regressions | pass |
| Targeted vitest (`--maxWorkers=4`): PracticeScreen*, AskOverlay*, screens/workbench, ReaderScreen.workbench, screens/practice, app | pass |
| `lint-imports --no-cache` | 36 kept, 0 broken |
| `npm run typecheck` | clean |
| `npm run frontend:build` | clean |

While the machine was loaded (load average about 118 from parallel stages),
the large vitest selection had a few timing failures. They were different on
each run, in `App.fixRound2`, `Workbench` F8 and `PracticeScreen.adaptiveHints`.
Each file passes when run on its own. The full suite runs at landing.

## Open questions for the owner

1. B2: are the fallback orders right? *Struggle*: an approach question, then
   "where it stops holding", then the item's hints. *Guide me*: the next step
   written for your work, before the item's hints. The workbench has the
   matching rung rules. Or should a Decider be routed for `hint_chooser`
   instead? The specs leave the style to the Decider alone.
2. B3: is a per-attempt Ask budget (3 questions per attempt) what you want,
   or should it stay per item per session?
3. B4: the attempts written under a successor key are unattributed. Is that
   acceptable, or should they be attributed to a fresh offer?

## Fix round 2 (Codex verify `20261025-145037-Wyei9F`)

The verify found three issues on `9b6300d13`. All three are fixed. Each has a
fail-first test in `tests/test_owner_capture_1025.py` (WIP commit
`d4faf6a28`; all five tests failed on `9b6300d13`).

### 1. Medium: a successor key bypassed the cross-session check

**What happened.** `submission_offer_answered_elsewhere`
(`src/learnloop/db/stores/collection.py`) found a key's intent by item alone.
Take a draft key from session A whose offer a steps attempt answered. Submitted
for the same item in session B with no offer, it was given the successor key
`<key>~after~<attempt>`. That key had no intent, so the bind accepted it as
new in session B. Before B4 the bind refused such a key ("The submission
belongs to a different item or session.").

**Fix.** The lookup now also requires the intent's session
(`i.session_id = ?`). `answering_key` passes the session, and so does
`recover_practice_submission`. A key from another session gets no successor,
and the bind refuses it as before.

**Test:** `test_fix2_a_key_from_another_session_is_refused_not_succeeded`. It
submits in session B and expects `validation_error`. It also checks that no
attempt and no successor intent were written, and that recovery in session B
reports `pending`.

### 2. Medium: a stale checkpoint's authored hint counted again

**What happened.** The fail-soft path replaced only `submission_id`. The
client's `hintsUsed` (and `authoredHints`) stayed the base of the fold. A
checkpoint the owner's bug already left behind restores `hintsUsed: 1` under
the answer box's key. That hint was shown before the steps attempt, and the
steps attempt already counted it. So the successor attempt, with no new help,
recorded one hint again. Clearing future checkpoints does not repair this
case.

**Fix.** `_without_stale_help` (`src/learnloop_sidecar/handlers/practice.py`)
runs in `submit_attempt_on` and `submit_dont_know_on` after the receipt
check. It applies when the submission takes the successor path, or when it
names an offer another attempt already answered (`_bind_offer`'s fail soft).
In either case the draft outlived an earlier attempt of the item, so the
help it carries does not count:
- **What is dropped.** The client's hint count, authored count, book flag and
  first-hint marker (`firstHintProgress`) are not used.
- **What counts instead.** Only help inside the item's window since its last
  attempt in this session counts. This is the server-side rule (H2b ruling R1).
  The server's rows count through the window fold, which this path turns on.
  The authored hints the screen revealed in that window count through their H0
  rows (`help_assists.authored_reveals_in_window`: distinct `authored_index`,
  any key, unattached). The total is never more than the client reports.
- **Logging.** A count that changes is logged as `stale_draft_help_dropped`.

`primed` is not dropped. On the practice screen it comes from how the item was
opened (a primed retry), not from the checkpoint.

**Tests:**
- `test_fix2_an_already_stale_checkpoints_hint_is_not_counted_again`. The
  stale checkpoint carries `hintsUsed: 1` and `authoredHints: 1`, with that
  hint's reveal row written before the steps attempt. The attempt records 0
  hints (1 on `9b6300d13`).
- `test_fix2_a_hint_revealed_after_the_earlier_attempt_still_counts` (guard).
  A second authored hint is revealed on the restored draft after the steps
  attempt, so the client sends 2. The attempt records 1 (2 on `9b6300d13`).
- `test_fix2_a_stale_offers_carried_hint_is_not_counted_again`. This is the
  fail-soft path: a new key names the offer the first attempt answered and
  carries that attempt's hint. It records 0 (1 on `9b6300d13`).

**What the owner should know.**
- With `hints.telemetry_enabled` off (it is on by default), no reveal row is
  written. An authored hint revealed on a stale draft then counts nothing:
  the server cannot tell it apart from the stale one.
- The authored-reveal rows are still telemetry everywhere else. This repair
  path is the only place a submit reads them, and it only ever lowers the
  client's count.
- The reveal rows written under the stale key are not attached to the
  successor attempt. The H0 attach matches by key, and the successor attempt
  has its own key. They stay unattached, outside every later window.

### 3. Low: a changed fallback kept the old policy version

**What happened.** B2's style-aware fallback changes decisions, but its rows
still recorded `hint-choice-policy-v1:fallback`.

**Fix.**
- `chooser.FALLBACK_POLICY_VERSION = "hint-choice-policy-v2"`.
- `chooser.policy_version(policy)` gives the row's version: a fallback
  choice records `hint-choice-policy-v2:fallback`, and the Decider's draws
  keep `hint-choice-policy-v1:<policy>`. `service.py` uses it for every
  served row, the workbench's included.
- `docs/specs/spec_adaptive_hints_v1.md` §4.5 ("Fallback") now gives the
  style-aware rules for the practice screen and the workbench, with the
  version. D3 records the amendment.
- Codex confirmed this needs no algorithm successor (§10.1): counts and
  `primed` keep their meaning.

**Test:** `test_fix2_a_changed_fallback_names_its_new_policy_version`.

### Gate

| Check | Result |
|---|---|
| Targeted pytest (`-n 6`, 5G scope; 75 files): the owner-capture file; every `test_hint_*`, `test_workbench_*`, `test_reader_rw2*` and `test_practice_*`; help-assists schema; collection dataset; sidecar contract; daily plan RPC and regressions; teach-back; router offer log; forecast receipts; facet outcome view; stuck prompt; architecture | 1085 passed, 8 skipped |
| Durability lane (`--durable-sqlite`): the owner-capture file, collection dataset, sidecar contract, daily-plan regressions, router offer log | 224 passed, 7 skipped |
| `lint-imports --no-cache` | 36 kept, 0 broken |

This round changed no client code, so vitest and the frontend build were not
rerun. No model, paid or live calls were made. The full suite runs at landing.
