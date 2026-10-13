# Codex review fixes: "Write what you can" (stage `practice-stuck-prompt`)

Branch `practice/stuck-prompt`, worktree `learnanything-stuck`. Codex reviewed
the stage at `5d9c1491` (job `~/.cache/codex-agent/jobs/20261012-131553-N6lOI9`):
1 High and 5 Medium findings. All six reproduced and are fixed. Each fix
started with a failing test (or, for F2's frontend half, tests shown to
fail against the unfixed screen). The stage's own write-up is
`docs/reviews/stuck-prompt.md`; this file covers only the review.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Multiple-choice grading can award full credit to confusion text | fixed | `c85fba2b` | `tests/test_stuck_prompt.py`: `test_a_stuck_answer_on_a_choice_item_goes_to_the_grader_not_the_letter_shortcut` (9 cases: prose starting with A, B, C, D, E, F, G, H, and "C, but I don't understand why"), `test_the_fallback_door_also_skips_the_letter_shortcut_for_a_stuck_answer` |
| F2 | Medium | Draft recovery loses the stuck marker | fixed | `0b90157d` | `tests/test_stuck_prompt.py::test_the_draft_checkpoint_keeps_the_stuck_marker_across_a_restart`; vitest `PracticeScreen.test.tsx`: "saves and mirrors the stuck marker with the draft", "saves the cleared marker when the learner steps back out of stuck mode", "reopens a restored stuck draft in stuck mode and submits it as a stuck answer", "never restores stuck mode where the vault does not offer it"; `practiceDraft.test.ts` (3) |
| F3 | Medium | Disabling split grading silently disables confusion detection | fixed | `6c1b9176`, `66c4193d` | `test_confusion_is_read_and_signalled_in_both_grading_modes[split, joint]`, `test_an_ordinary_joint_answer_keeps_its_prompt_and_hash_exactly`, `test_a_joint_regrade_rereads_the_stuck_answer_and_supersedes`; `tests/test_stuck_prompt_replay.py::test_a_joint_stuck_reading_survives_rebuild_with_no_model_call` |
| F4 | Medium | Empty TUI submissions do not reveal the answer | fixed | `07c65e24` | `test_tui_empty_stuck_submit_shows_the_result_and_the_worked_answer`, `test_tui_empty_stuck_probe_answer_keeps_feedback_deferred` |
| F5 | Medium | The paid stuck command lacks spend admission and a dry run | fixed | `f45f737a`, `780bec29` | `test_cli_stuck_dry_run_estimates_the_grading_calls_with_no_call_and_no_write`, `test_cli_metered_stuck_grading_is_refused_before_any_call_without_a_price`, `test_cli_metered_stuck_grading_is_admitted_and_charged_with_a_price`, `test_cli_subscription_grading_counts_calls_without_a_token_bound` |
| F6 | Medium | The confusion classification never reaches `judgment_ledger` | fixed | `9ac08a5c` | `test_the_stuck_reading_appends_a_judgment_with_the_blind_record`, `test_a_regrade_appends_a_superseding_stuck_judgment` |

Rejected: none.

The three "claims that don't hold" are now true: a non-empty stuck answer
always reaches the grader (F1); the paid command door is admitted on caps
and has a dry run (F5); the reading is a `judgment_ledger` verdict (F6). The
conformance note on the replay tests is also addressed (`66c4193d`).

## What changed

### F1: no option-letter shortcut for a stuck answer

`_try_deterministic_grade` returns nothing for a declared-stuck draft, so
both doors (required and fallback) send it to the grader. With no grader
ready, the fallback door uses the learner's self-grade, never "Correct,
option C". Ordinary letter answers keep the free shortcut.

Reproduced first: "Confused about why the last factor is transposed" on a
choice item whose answer is C scored 4/4, `grading_source = deterministic`,
with no grading call. Prose starting with A, B or D failed the same way.

### F6: the reading is a verdict

`attempts.stuck.record_stuck_reading_judgment` appends one row:

- `task = "stuck_reading"`, `left_kind = "attempt"`, `left_id` = the attempt,
  no right-hand entity;
- `judge = "llm"` with the resolved model;
- the grader's prompt version (`...+stuck-v1`);
- `input_hash` = the grading context hash (the blind record's `context_hash`
  in split vaults);
- `verdict` = the verified reading as JSON: `attempts_answer`,
  `describes_confusion`, `confusion_quote`, `quote_verified`, `version`;
- a one-line rationale.

It is written in the transaction that records the grade (and, blind, its
blind record). A regrade, blind or joint, appends a judgment that supersedes
the current one.

`stuck_answers()` reads the current judgment back (new field
`judgment_id`). It falls back to a blind record's reading only for grades
recorded before this fix. The confusion signal follows the same reader, so
the learner-text-gaps stage has one place to read the confusion text and its
marker.

### F3: the joint grader reads stuck answers

- `GradingContext` gains `answer_prompt`. When it is absent, it is omitted
  from the rendered prompt and from `grading_context_hash`. Checked against
  the pre-fix module: an ordinary joint prompt is byte-identical (11,077
  characters).
- A stuck answer in a joint vault gets the same stuck rules appended to the
  joint task. Its prompt version is `GRADING_PROMPT_VERSION+stuck-v1`.
  `StuckGradingProposal` returns the reading last.
- The reading is verified, removed from the applied proposal, and appended
  as the F6 judgment in the grading transaction.
- A joint regrade re-reads the answer and supersedes the old judgment. The
  Phase C receipt records the prompt version that actually ran.
- The calibration identity stays the joint grader's, because the scoring
  rules are unchanged. This matches the blind path.
- A legacy endpoint adapter never sees the prompt, so it keeps the plain
  model. Its JSON context now also carries `"answer_prompt": null` (an added
  key).

This closes the stage review's open question 2 ("Joint grading").

### F4: the TUI shows the result

In ordinary TUI practice, an empty stuck submit:

1. records the deterministic zero;
2. opens the feedback screen on that committed result. No grader runs, no
   self-grade form appears, and the post-attempt pipeline runs with no model
   client.
3. shows a "Worked answer" block with the item's answer.

Inside a diagnostic check, feedback stays deferred as it was for "I don't
know": the answer is recorded and the screen returns to Today. The stuck
banner says which of the two will happen.

### F2: the marker survives recovery

- **Sidecar:** `save_practice_draft` takes `declaredStuck`. It is stored as
  `practice.declaredStuck` in the checkpoint's practice envelope, beside the
  retry key, so no migration is needed. Only a stuck draft carries the key,
  so a later item never inherits it. The checkpoint DTO returns
  `declaredStuck`. An older client that never sends it reads as not stuck.
- **Desktop:** `PracticeScreen` saves the marker with every draft flush,
  including stepping back out of stuck mode. It reopens a restored stuck
  draft in stuck mode, but only where the vault offers "I'm stuck". App's
  in-memory draft mirror carries the marker; `restoredPracticeDraft`
  (`app/practiceDraft.ts`) holds that logic.
- **Rust:** no change; the command is a passthrough.

### F5: dry run and admission on the paid command

`learnloop attempt` is the door that sends paid grading from the command
line (with `--stuck` or without). It now uses the Phase 1 framework:

- **Planning.** `plan_grading_calls()` assembles exactly what the door would
  send, with no call and no write. The joint prompt is still rendered only
  in `grading.py` (`joint_grading_prompt_tokens`), which keeps the
  grading-door guard test intact (`780bec29`):
  - an empty stuck answer, or an option letter on an ordinary answer, makes
    no call;
  - otherwise the blind or joint prompt makes one call per sample.
- **Dry run.** `--dry-run` prints that plan with no client, no call and no
  write (read-only repository):
  - calls, estimated input tokens, and the output limit;
  - metered tokens and USD;
  - route billing and `cost_basis`;
  - `admissible` and the reason.

  It exits 1 when the plan is not admissible. It also lists the conditional
  inline diagnosis with its own per-job caps and `diagnosis.max_calls_per_day`.
- **Admission before anything is sent.** A real run checks the whole plan
  first. If it does not fit, the command exits 1 with `over_budget` and
  nothing is sent or recorded. The self-grade prompt now comes after this
  check, so a refused run asks for nothing.
- **Admission per sample.** Each sample is then admitted through
  `ReviewSpend` over the shared `SpendBudget`, via an opt-in
  `grading_admission` guard around each grading call. The guard is a no-op
  on the desktop, TUI and sidecar doors.
  - Metered routes: transport retries and JSON repairs are admitted as they
    start, and an unknown price fails closed unless `--price-per-million` is
    given.
  - Codex on the owner's subscription: calls are counted. There is no
    physical-request, token or dollar bound, and tokens are recorded from
    reported usage as `estimated_only`.
- **Caps.** `--max-calls 10`, `--max-retries 4`, `--max-tokens 250000`,
  `--max-cost-usd 1.0`.
- **Output.** The JSON result includes `spend`. The command still owns its
  model-call receipts: the spend collector forwards them through
  `cli.receipts.current_command_recorder`.

**Estimates.** The input estimate is prompt bytes / 4, the same rule the
diagnosis plans use. Codex reported about 16k–24k input tokens per turn
against estimates of 3.8k–4.5k, because its harness adds its own context.
On the subscription this only affects the `estimated_only` figure. A metered
route reconciles to reported usage after each call, so an underestimate
stops the next request rather than the current one.

## Live verification (backup-API copies, Codex subscription)

Both copies are under the worktree's `fixtures-local/`:

- `stuck-linear_algebra`, at mvp-0.11 from the stage run;
- `stuck-linear_algebra-joint`, a new `copy_tree_with_databases` copy of it
  with `[diagnosis] split_enabled = false` appended.

Each run took a `--dry-run` first. The tracked fixture vaults were never
touched.

| Run | Dry run | Result | Grading wait (`agent_runs`) | Tokens in / out |
|---|---|---|---|---|
| Split, `pi_axiom_commutative_recall_02`, partial + confusion ("I think it's u+v = v+u but I'm not sure whether it needs 'for all'...") | blind, 1 call, ~3,773 input tokens, subscription, admissible | 2 / 4, `codex`. Reading: attempts the answer, describes confusion, quote verified. Judgment written (`gpt-5.6-sol`, `mvp-2.1-blind-reference-policy+stuck-v1`). Spend: 1 call, 0 metered tokens. | 24 s | 16,277 / 1,343 |
| Joint, `pi_axiom_closure_recall_01`, confusion only ("I don't understand what V×V means here...") | joint, 1 call, ~4,488 input tokens, `mvp-1.5-...+stuck-v1`, admissible | 0 / 4, `codex`. Reading: no attempt, describes confusion, quote verified. Judgment written, no blind record. `stuck_confusion` signal on `lo_operations_and_the_vector_space_axiom_checklist`, mass 0. | 27 s | 23,978 / 1,636 |

Calls: 2 Codex grading turns on the owner's ChatGPT subscription
(`estimated_only`). Both used `--no-diagnose` or ran in joint mode, so no
diagnosis call was made. No OpenRouter or other metered call was made, and
the metered spend was $0.

**The wait (P7).** A stuck answer with text waits for the synchronous grade:
24–27 s here, and 29–37 s in the stage's runs, under the copies'
`ai.timeout_seconds = 60`. An empty stuck answer makes no call and is
recorded at once (0.4 s in the stage run; that path is unchanged).

## Gate

Run on `d617a507`, the code of this review's commit.

| Step | Result |
|---|---|
| `uv sync --extra dev`, `uv pip install pypdfium2` | done (no mobile change, so no `--extra mobile`) |
| `uv run lint-imports --no-cache` | **10 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7326 passed**, 0 failed (196 s). The first run, on `d95d16cd`, had 1 failure (7325 passed): `test_only_the_joint_doors_call_the_joint_grading_operation`, because `plan_grading_calls` rendered the joint prompt outside `grading.py`. `780bec29` fixed it, and this run is on `d617a507`. |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **80 passed**, 7246 deselected (89 s) |
| Frontend (`apps/learnloop-tauri`): `npm install`, `npm run typecheck`, `npm test`, `npm run frontend:build` | install ok (esbuild's install script blocked by npm's allowScripts, as before); typecheck clean; **88 passed in 21 files**; build ok. Run at `d95d16cd`; nothing in the frontend changed after it. |
| DB reference: `db_generate_reference.py`, then `db_validate_reference.py` | `errors: []`. There is no schema change, but the validator reported 13 stale source-line citations from the moved code, so the reference was regenerated (`d95d16cd`, then `d617a507`). `validate_vault.py` passed (1,044 notes). |

`/tmp` (tmpfs) was full during this run, so every command ran with `TMPDIR`
on disk (`~/.cache/learnloop-stuck-tmp`).

`module_validate.py` and `desktop_validate.py` already fail on the stage's
base: the module reference is about 200 notes behind, and the desktop map
lacks `TypeScript/screens/today`. Neither is part of the gate, and this
review did not change them.

## Files touched

- **Python:**
  - `attempts/`: `attempts.py`, `ai_contracts.py`, `grading.py`,
    `grading_support.py`, `regrade.py`, `stuck.py`, and the new
    `grading_admission.py`;
  - `cli/app.py`, `cli/receipts.py`;
  - `diagnosis/diagnostic_augmentation.py` (the receipt's prompt version);
  - `field/signals.py` (docstrings);
  - `tui/screens/practice.py`, `feedback.py`, `feedback.tcss`;
  - sidecar `context.py`, `handlers/practice.py`, `handlers/sessions.py`.
- **Frontend:** `api/client.ts`, `api/dto.ts`, `app/App.tsx`, the new
  `app/practiceDraft.ts` with its test, and `screens/PracticeScreen.tsx`
  with its test.
- **Tests:**
  - `tests/test_stuck_prompt.py`: 20 → 43;
  - `tests/test_stuck_prompt_replay.py`: 3 → 4, and the first test now
    compares live state against the first rebuild;
  - `tests/cli_help_snapshot.json` (`attempt`).
- **Docs:** the regenerated DB and config reference, and this file.
- **Migrations:** none. 172 is unchanged.

## Owner-run commands

On a `fixtures-local/` copy first:

```bash
uv run learnloop attempt <item> --stuck --answer "..." --dry-run --json --vault <vault>   # plan + estimate, no call
uv run learnloop attempt <item> --stuck --answer "..." --vault <vault>                   # admitted on the caps
uv run learnloop attempt <item> --stuck --answer "..." --price-per-million <usd> --vault <vault>  # metered grading route
uv run learnloop field data-check --json --vault <vault>                                 # stuck_answers: share with text, grading wait
```

## Open questions

1. **The option-letter parser outside stuck answers.** `_option_letter`
   accepts any leading A–H letter with no word boundary. An ordinary
   (non-stuck) free-text answer such as "Because ..." on a choice item
   therefore still parses as option B. That predates this stage, so it is
   left alone: only stuck answers are fixed here. Tighten the parser in its
   own change?
2. **Spend admission on the learner-facing doors.** Only the command
   (`learnloop attempt`) is admitted. The desktop, TUI and sidecar practice
   doors grade synchronously as before, with no caps beyond the provider's,
   as in Slice 1 M2. Admitting them would put a metered route with an
   unknown price in front of the learner. Leave them as they are?
3. **Ordinary `learnloop attempt` on a metered route** is now refused unless
   `--price-per-million` is given. The owner's grading route is Codex, so
   nothing changes for the owner's vaults.
4. The stage review's open questions 1 and 3–7 still stand. Question 2
   (joint grading) is resolved by F3. (At the merge, 2026-10-12: the owner
   answered question 1, an empty stuck answer is a bare 0 with no error
   tag; the merge settled 4, new vaults start at the latest version, now
   `mvp-0.13`, and 7, the relabel and renumber. See the integration note in
   `docs/reviews/stuck-prompt.md`.)

## Re-review

Codex re-reviewed the fixes at `2085a650` (job
`~/.cache/codex-agent/jobs/20261012-143008-sNBhb4`, verdict REOPENED). It
confirmed F1 fixed: 18 in-memory checks of prose starting with A–H, and of
mixed option and confusion text, through both the required and the fallback
doors, made zero option-letter parser calls. It raised two new Medium
findings, F7 and F8. Both reproduced with a failing test first, and both are
fixed.

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Multiple-choice grading can award full credit to confusion text | fixed (confirmed by the re-review; no change in this step) | `c85fba2b` | as in the first table |
| F7 | Medium | Spend-limit refusal silently becomes a self-grade | fixed | `e8187f25` | `tests/test_stuck_prompt.py`: `test_cli_a_retry_refused_by_the_caps_is_over_budget_not_a_self_grade`, `test_cli_a_later_sample_refused_by_the_caps_is_over_budget_not_a_self_grade` |
| F8 | Medium | New TUI answer reveal leaves subsequent evidence unprimed | fixed | `57c8c899` (reference `b9ad148a`) | `tests/test_stuck_prompt.py`: `test_the_tui_worked_answer_is_recorded_as_a_reveal_and_primes_the_retry`, `test_a_worked_answer_shown_in_the_attempts_own_second_still_primes_the_retry`, `test_only_post_attempt_displays_cross_the_same_second_boundary`, `test_migration_173_widens_the_reveal_kinds_and_keeps_the_ledger` |

Rejected: none.

### F7: a spend refusal mid-grade is over budget

**Reproduced.** Two cases, both on a metered fake grader with
`--price-per-million 2.0`:

- a sample whose second physical request (a transport retry) is refused by
  `--max-retries 0`;
- a second blind sample (`[diagnostic_augmentation] sample_count = 2`)
  refused by the token cap, after the first sample reported 400,000 input
  tokens against its estimate.

Both exited 0 with `grading_source = "self"` and
`fallback_reason = "ai_failed:SpendLimitExceeded"`. The command had recorded
the supplied self-grade as the attempt.

**Fix.** The fallback door
(`_complete_attempt_with_agent_fallback`) catches `SpendLimitExceeded`
before its generic `ValueError` handler. It closes the grading run as
`failed` with the refusal message (its tokens are recorded) and re-raises.
`learnloop attempt` then:

- exits 1 with `status = "over_budget"` and the refusal message;
- records no attempt and no self-grade;
- adds `spend` (the calls already sent, their metered tokens and USD) to the
  JSON. The text output says "Already sent: ... Nothing was recorded."

The required door already re-raised every grading error, so it needed no
change. The guard is installed only by the command, so the desktop, TUI and
sidecar doors cannot raise this.

### F8: the TUI's worked answer is a reveal

**Reproduced.** After an empty stuck submit in the TUI, the feedback screen
showed the worked answer and `reveal_events` had no row. A retry right after
it was recorded unprimed.

Writing the row alone was not enough. Timestamps have one-second
resolution, and the submit window starts strictly after the last attempt
(`created_at > since`). A display stamped in the attempt's own second, which
is the usual case here (1.7 s from submit to feedback), fell outside the
next attempt's window. The TUI test (real clock) and a frozen-clock test
both still failed with the row written and the old window.

**Fix.**

- **Migration 173** (`173_answer_display_reveal.sql`) rebuilds
  `reveal_events` with the source kind `answer_display`: the expected answer
  itself, shown on a feedback screen. Every row, both indexes and both
  append-only triggers are kept. The `source_kind` CHECK allows none of the
  existing four kinds for this exposure, and borrowing `repair_display`
  would mislabel it.
- **The writer.** `reveal_ledger.record_answer_display_reveal` charges 1.0
  (the full answer) once per attempt. The row is linked to the item, its LO,
  any live repair episode, and the committed attempt; its basis is
  `worked_answer:stuck_empty:tui`. Like every ledger writer, it is best
  effort.
- **The TUI** records it when the worked answer becomes visible (feedback
  mount on a committed empty stuck answer). Inside a diagnostic check the
  answer is not shown, so nothing is recorded there.
- **The window.** `reveal_total_for_submission` also counts rows of
  `POST_ATTEMPT_REVEAL_KINDS` (only `answer_display`) linked to the last
  attempt, even when they are stamped in that attempt's own second. Such a
  row is written after its attempt by construction. Every other kind keeps
  its window exactly, so vaults that never write `answer_display` behave as
  before; `test_only_post_attempt_displays_cross_the_same_second_boundary`
  pins that. Open question 5 asks whether to widen it.
- **The head fixture** `migration_head_172` is now `migration_head_173`,
  upgraded and kept in rollback mode. Its README, the six test paths and the
  two reference scripts (`SCHEMA_HEAD = 173`) are updated, and the DB
  reference is regenerated (`b9ad148a`). Main is at 170 and mobile M1 takes
  171, so 172 and 173 are this stage's; expect renumbering at merge.

### Manual run (backup-API copy, no paid call)

`fixtures-local/stuck-linear_algebra-f8b` is a `copy_tree_with_databases`
copy of `fixtures-local/stuck-linear_algebra` (mvp-0.11, migration 172).
The TUI was driven headless with Textual's `run_test`:

- opening the copy applied migration 173;
- an empty stuck submit on `pi_axiom_closure_recall_01` recorded a
  deterministic 0 and showed the worked answer, 1.71 s from submit to
  feedback (the post-attempt pipeline included, no model call);
- one reveal row: `answer_display`, 1.0, linked to that attempt;
- a self-graded retry of the same item was recorded `primed` with
  `auto_primed_reveal_total = 1.0`.

A first copy, `stuck-linear_algebra-f8`, stopped after the TUI half: the
script picked an attempt type that item does not allow. Neither copy is
tracked. No model call, paid or subscription, was made in this step, so the
cost is $0. The tracked fixture vaults were not touched.

**The wait (P7) is unchanged.** A non-empty stuck answer waits for the
synchronous grade: 24–37 s measured across this review and the stage runs,
under `ai.timeout_seconds = 60`. An empty one makes no call: 0.4 s through
the command, and 1.7 s to the TUI feedback screen.

### Re-review gate

Run on `b9ad148a`, the code of this section's commit. Only this section
of the review file changed after it.

| Step | Result |
|---|---|
| `uv sync --extra dev`, `uv pip install pypdfium2` | done (no mobile change, so no `--extra mobile`) |
| `uv run lint-imports --no-cache` | **10 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7332 passed**, 0 failed (226 s). That is 7326 plus the 6 new tests; `tests/test_stuck_prompt.py` goes from 43 to 49. |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **80 passed**, 7252 deselected (60 s) |
| Frontend | not run: nothing under `apps/learnloop-tauri` changed in this step. The first gate's 88 vitest passes stand. |
| DB reference: `db_generate_reference.py`, then `db_validate_reference.py` | `errors: []` with the schema at migration 173 (`SCHEMA_HEAD = 173`); regenerated in `b9ad148a` |

As before, every command ran with `TMPDIR` on disk
(`~/.cache/learnloop-stuck-tmp`). The full suite waited for the shared lock
behind another stage's run.

### Open questions added by the re-review

5. **Same-second reveals of the other kinds.** A `repair_display` or
   `tutor_answer` row linked to the last attempt and stamped in its second
   is still outside the next attempt's window. Only `answer_display` gets
   the attempt-link rule here, because widening it changes auto-prime for
   existing vaults (an admissibility change, so the playbook applies).
   Widen it to every attempt-linked post-attempt kind?
6. **The TUI's ordinary self-grade form** shows "Expected: ..." for every
   ordinary answer, and that display writes no reveal either. This predates
   this stage and is left alone. Charge it too?
7. **"We could also do this for errors/misconceptions too"** (the owner's
   note relayed with this run). This fix step closes F7 and F8 only. Applying
   the stuck reading to errors and misconceptions, for example marking
   stated misconceptions in stuck text, fits the planned learner-text-gaps
   stage, which reads the confusion text and its marker through
   `stuck_answers()`. Which did you mean?
