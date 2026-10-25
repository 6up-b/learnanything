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

## Landing onto main

Branch `merge/capture-fixes-onto-main` in `learnanything-merge2`. It was cut from `main` at `0db8291c1` (mobile PR-1
secondary attach and two docs-only specs). Main did not move during the gate. **No algorithm successor, no
migration, no config key.** Main was neither fast-forwarded nor pushed.

### Commits and conflicts

- `70b1c6067`: the `--no-ff` merge of `fix/owner-capture-1025` (`2ffa46b02`). **No conflicts.** PR-1 changed
  `src/learnloop_sidecar/context.py`, `remote/runtime.py`, `vault/loader.py` and `db/migrate.py`. This stage changed
  the practice, workbench and tutor handlers, `hints/*`, `db/stores/collection.py` and the practice and workbench
  screens. The two sets of files do not overlap.
- `a1889c49f`: the regenerated reference notes (below).
- This record (docs only).

The diff against main adds five files: this record, `tests/test_owner_capture_1025.py` and three vitest files. It
adds no database or binary file, and the root `.gitignore` is unchanged.

### Regeneration

- **References.** On the merge, `db_validate_reference.py` failed with **4 errors**: the `tutor_qa.max_questions_*`
  citations still named `src/learnloop/tutor/tutor_qa.py` lines from before the stage (298/303/310/318, now
  323/328/335/343). The stage had not regenerated them. `db_generate_reference.py` was rerun and 5 notes with a
  real change were kept:
  - `Config - tutor_qa`: the citations.
  - The `help_assists`, `scheduler_slate_candidates`, `session_checkpoints` and `submission_intents` table notes:
    their source/test lists now name `tests/test_owner_capture_1025.py`, and `session_checkpoints` also names
    `handlers/workbench.py`.

  The other 418 rewrites changed only `source_commit` and were discarded. After that, the validator reports
  **0 errors**.
- **CLI help snapshot, RPC pins, defaults snapshots:** no change.
  `test_cli_help_snapshot`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_registry`,
  `test_config_refactor`, `test_architecture`, `test_public_tip_guards` and the stage's file gave 96 passed with no
  file changed, and they pass again in the full suite.
- **`validate_vault.py`**: passes (1,155 notes, 1,153/1,153 reachable).

### Gate

Setup: `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` (5.14.0) in 5G scopes. The pytest lanes
ran in 10G / 2G swap scopes under `flock /tmp/learnloop-fullsuite.lock`. Everything else ran in 5G / 1G scopes.
Every Python run used `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, and all three
directories existed beforehand. Logs are in `fixtures-local/capture-landing/`.

| Step | Result |
|---|---|
| `lint-imports --no-cache` | **36 kept**, 0 broken |
| full suite (`pytest -n 8`, at `a1889c49f`, 1 h 05 min) | 21,402 passed, **1 failed**, 74 skipped (the owner lane), 38 xfailed |
| the one failure, run alone 3 times | `test_plan_first_transport_offer_grants::test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter`: **3/3 passed** (44 s each). It is a known load flake, and this stage does not touch the transport |
| durability (`-m durability`) | **124 passed**, 1 skipped |
| `npm install`; `npm run typecheck` | ok; clean |
| `npm test -- --maxWorkers=4` (whole vitest) | **213 files, 1,832 tests passed**. The timing flakes the stage saw under load (App.fixRound2, Workbench F8, PracticeScreen.adaptiveHints) did not recur |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished |
| worktree, tracked fixtures | `git status` clean apart from `fixtures-local/` |

The Codex lockdown files all pass in the full suite, because the empty `CODEX_HOME` existed this time.

### Parity (backup-API copies; no real model call)

**Setup.** Scripts are in `fixtures-local/landing-capture/scripts/` (PR-1's, re-pathed) and
`fixtures-local/landing-capture/scripts_cap/` (new for this landing).
- `orig/` holds backup-API copies of `learnanything/fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}`.
- `u31/` is `orig` brought to **mvp-0.31 with main's code**: every route neutralized to a `127.0.0.1:9` blackhole,
  then `upgrade --to mvp-0.31` and `rebuild-derived-state` twice.
- `code_main` and `code_merge` are `git archive` exports of `0db8291c1` and of the merge.
- `run.py` puts the chosen code first on `sys.path`. Its audit hook refuses any process start that mentions codex
  and any non-loopback socket. Over every parity run it logged **no process start and no connection at all**.
- `~/learnloop-vaults` was never opened.

**(a) Main vs merge, no practice actions** (`scripts/a.sh`; a second main copy, `c31r2`, is the noise control).
Both vaults went through the normal primary sidecar load at a frozen clock with deterministic ids.
- Whole databases: **identical** (schema and every row of 356 tables, 8,208 rows on probability; `row_differs` and
  `sql_diffs` empty on both vaults). Integrity is ok, and `model_call_receipts` is 0 on both sides.
- `rebuild --shadow` and `doctor`: **0 differences** main vs merge on both vaults. The shadow's 30 schedule
  differences from live on linear_algebra, and doctor's issue counts (57 / 1 error and 101 / 48 errors), are the same
  on both sides. They predate this stage.
- Certification, curves, Today and the plan at the frozen clock: **byte-identical** main vs merge and main vs main
  on both vaults (linear_algebra cert 129,651 / today 528,665 / plan 84,714 bytes; probability 17,495 / 741,269 /
  40,799).

**(b) The owner's scenario through the real sidecar** (`scripts_cap/cap_run.py`; each run on a fresh copy of
`u31/probability`).
- **How it ran.** `cap_sidecar.py` runs `learnloop_sidecar.server.serve` over stdio JSON-RPC with
  `LEARNLOOP_HINT_MODELS=off`. Only three roles are fakes: the grader (`StuckFake`), the practice tutor (a recording
  fake that keeps every context it is given) and the hint writer (`WriterFake`, injected the way the tests inject
  it). The chooser therefore takes the fallback, which is the owner's no-Decider case.
- **The item** is the owner's `pi_exercise_01kyn2kdf7h2kba1fp7wv7t3w5` (4 authored hints), served from the queue
  with its offer.
- **`fixed` = the merged client's behaviour.** Hint (server ladder) → Work in steps (2 steps) → Ask (the steps sent
  as `learnerDraftMd`) → submit in steps → the item served again (new key, Hint, Ask) → submit in the answer box.
- **`stale` = the owner's original chain** (the old client). The answer box's draft also carries one
  client-revealed authored hint (`hintsUsed: 1` plus its H0 row). After the steps submit, the **old** key is
  resubmitted with the restored `hintsUsed: 1` and no offer.

| | main `0db8291c1` | merge |
|---|---|---|
| Ask in steps | answered. The tutor's prompt held both steps, because the server already took `learnerDraftMd` (B1 was client-only; its vitest pins the client) | answered, both steps in the prompt |
| checkpoint after the steps submit | still the item, with the answer box's draft | **cleared** |
| Ask thread when the item comes back | the earlier question, 2 of 3 left | **empty, 3 of 3 left** |
| after a second Ask on the reattempt | both questions, 1 left | **only the new one, 2 left** |
| Hint on the reattempt (new key) | authored hint 1 again (rows are read by key) | authored hint 1 again: a fresh ladder |
| answer-box submit, `fixed` | graded, attributed to the new offer | graded (`gradingSource: ai`), attributed to the new offer |
| answer-box submit, `stale` (old key) | **`validation_error: The scheduler offer does not belong to this item/session or was already consumed.`** No attempt | **graded** under `box-1~after~<steps attempt>`, unattributed, `hints_used` **0** (fix round 2, item 2) |
| hint counts, `fixed` | steps attempt 2 (1 server hint + 1 Ask), reattempt 2 (1 hint + 1 Ask) | the same. Each attempt counts only its own help. The hint-equivalence window was already per attempt |
| hint counts, `stale` | steps attempt 3 (server hint + carried client hint + Ask) | steps attempt 3; the successor attempt **0** |
| hint rows' attempts | each server row attached to its own attempt | the same. The stale draft's client row stays unattached, as the review says |
| answered offers | each offer keeps exactly one attempt | the same. The successor attempt never takes the consumed offer |
| hint `policy_version` | `hint-choice-policy-v1:fallback` | `hint-choice-policy-v2:fallback` |

**(c) The help style with the fallback chooser** (the item, one Hint press after `practice.set_help_style`; and in the
workbench, one suggestion after `workbench.set_help_style`).

| style | main, practice | merge, practice | main, workbench | merge, workbench |
|---|---|---|---|---|
| balanced | authored hint 1 (L3) | authored hint 1 (L3) | rung 1 `approach_question` | rung 1 `approach_question` |
| let me struggle | authored hint 1 (L3) | **`approach_question` L1** | rung 1 | rung 1 |
| guide me | authored hint 1 (L3) | **`next_step` L3** (written for the work) | rung 1 | **rung 3** (the item's authored hint) |

The merge's rows record `help_style` and `hint-choice-policy-v2:fallback`. These are the first hints documented in
§4.5 and in `styled_level`. Main serves the same first hint for every style, which is the owner's B2.

**Receipts.**
- Every copy in (a): 0 receipts.
- The (b) and (c) copies: only the fakes' rows (`fake`, `fake_tutor`, `fake_writer`). No real provider row,
  completed or otherwise.

### Owner notes: what changes for the learner

- **Ask works in Work in steps.** There is an "ask · ?" action and the `?` key, and the tutor sees your steps as
  your work.
- **The help style matters without a Decider.**
  - *Let me struggle* starts with an approach question.
  - *Guide me* starts with a next step written for your work.
  - *Balanced* is unchanged.
  - In the workbench, *guide me* suggests rung 3 first, and *let me struggle* never suggests worked help.
  - Changing the style with the ladder open asks for a new suggestion.
- **A reattempt starts fresh.** A new hint ladder, a new Ask thread, and 3 Ask questions per attempt. Earlier hints
  and questions stay on record and count only on the attempt they belonged to.
- **Submitting never fails on a stale offer.** A draft the old bug left behind is graded, unattributed. Help from
  before the earlier attempt is not counted again.

### Open items

- Three owner questions are recorded at the orchestrator's defaults:
  - the style-aware fallback orders as built (long term: a model-routed `hint_chooser`);
  - the 3-question Ask budget is per attempt;
  - a successor-key submit is graded unattributed.
- The Ask UX overhaul (the owner's 11:00 note) is a separate design item.
- From the stage's own notes:
  - With `hints.telemetry_enabled` off, an authored hint revealed on a stale draft counts nothing.
  - The stale key's reveal rows stay unattached.
