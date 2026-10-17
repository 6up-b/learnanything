# One serve/administration eligibility decision

**Stage:** `serve-eligibility-decision`, queued by the orchestrator on 2026-10-16. The brief is UX Phase 4's Codex review, §12.9 (with its reproduction) and §13.6 (callers on a frozen or past clock, Q33), `docs/reviews/ux-phase4-feedback-codex-review.md`.
**Branch:** `serving/one-eligibility-decision`, from main `a26284876` (mvp-0.26, migrations to 206).
**Commits:** `3c5f0cbca` (the decision, every path routed, tests, the pipeline map), `f0d3de361` (the CLI persists its re-time only after the draft passes), then this record.
**No successor, no migration** (207 stays free), no config key, no RPC name, no frontend change. Grading, regrade and replay are untouched.
**Paid calls:** none. Every test uses fakes. The parity runs read backup-API copies with an empty config directory, so no model could be reached.

## 1. The cause

Every serve path asked its own question of the reveal ledger, and they disagreed.

- **Submit** (`attempts._resolve_attempt_target`, through `auto_primed_draft`): a non-routine reveal (a tutor answer, a repair display, a guided redo, a source re-read) counts from the item's **last attempt**, with no lapse. Only an attempt absorbs it. A cold check whose answer is primed is refused: "a cold retry must be unassisted and unprimed".
- **The queue's cold lane** (`scheduler._defer_revealed_cold_followups`): the same kinds count only from the **task's creation**, for one cold delay (D = 1 day).
- **The serve-time hold** (`cold_check_serve_hold`, used by the plan, the pick, the session serve, `open_queue_item` and the TUI): routine displays only (round-6 ruling 2).

**§12.9's reproduction.** A cold retry on `pi_cold` was created a day ago and has been due for an hour. A `tutor_answer` reveal of the item was made 26 h ago, before the task. The cold lane and the plan serve it as `cold_retry`. Submit then primes the answer and refuses it, after the learner has written it. The task stays due, so every serve walks into the same refusal until it expires (`right_censored_expired`).

**The CLI.** `learnloop attempt` prompted for the answer (`typer.prompt`) and only then validated the draft (`plan_grading_calls`). So it refused only after the learner had typed. §12.9's reproduction was `--attempt-type diagnostic_probe` on a basic vault; a cold check that submit refuses behaved the same way.

**Found on the way.** Five completion doors (`_complete_attempt_with_agent_fallback`, `_complete_attempt_with_agent_required`, `complete_self_graded_attempt`, `complete_empty_stuck_attempt` and `complete_codex_graded_attempt`) validated against the system clock, not the clock they were given. Submit's "now" and the record's "now" could differ for a caller with a frozen clock. Every door now passes its clock to the validation (§6).

## 2. The function

`src/learnloop/serve_eligibility.py` is a leaf: stdlib plus `learnloop.reveal_coverage`, like that module. So `attempts`, `scheduling`, `diagnosis`, the daily plan and the adapters can all import it without a new contract edge or a function-local cross-domain import. `lint-imports` keeps 22 of 22; `test_architecture`'s inventory is unchanged.

**Functional core.** `decide(inputs, request) -> EligibilityDecision` is pure.
- **The inputs** (`EligibilityInputs`) are:
  - the item and its learning object;
  - the instant (`at`);
  - the item's and the learning object's reveal rows, at every stamp;
  - the item's last attempt as submit reads it;
  - the open follow-up tasks of every kind selecting the item;
  - the bounded window `window_until` (Q33, §5);
  - the draft's own disclosure rows, which are exempt;
  - the draft's declarations: `declared_primed`, `hints_used` and `attempt_type`.
- **The record.** The decision is a record: the request, the verdict, a reason code, `until`, submit's total and `primed`, the reveal ids and task ids behind it, and the re-times (task id → new `not_before`). It has a plain message and `record()` for the trace.

**Imperative shell.**
- `gather(repository, …)` reads the inputs. It uses two new read methods on `Repository`: `open_followup_tasks_for_item`, and `list_recent_attempts_by_practice_item(…, until=)`, whose query is unchanged without `until`.
- `retime` applies the re-times through `defer_followup_task`. That push is monotone and never touches the expiry.
- `log_decision` writes the record at the path that acted on it: info for a verdict other than serve, debug for a serve.

**The constants have one definition**, in the leaf: `AUTO_PRIME_REVEAL_THRESHOLD`, `COLD_FOLLOWUP_TASK_KINDS`, `POST_ATTEMPT_REVEAL_KINDS` and `COLD_RETRIEVAL_DELAY`. `attempts` and `reveal_ledger` re-export the same objects, and a test pins the delay equal to `diagnosis.remediation`'s.

**Requests and verdicts.**

| Request | Asked by | Verdicts |
|---|---|---|
| `submit` | submit's admissibility, the CLI before it prompts | `serve` (admissible; primed as the ledger says), `refuse` |
| `cold_check` | every path that serves a cold follow-up | `serve`, `serve_as_ordinary`, `defer_until(t)` |
| `probe` | every probe or placement presentation commit and serve | `serve`, `refuse` |
| `quick_check` | the placement quick check's offers | `serve`, `refuse` |

**Reason codes.**

| Code | Verdict | Meaning |
|---|---|---|
| `eligible` | serve | nothing holds it back |
| `no_cold_check` | serve | a cold check was asked for, but no open cold task selects the item |
| `cold_check_routine_display` | defer_until | a routine display covers the item or its learning object (D + G), or submit's priming comes only from routine displays: time alone clears it. Unchanged code |
| `cold_check_revealed_since_scheduled` | defer_until | a non-routine reveal on the item or its learning object since the task was created, for one cold delay (the scheduler's own deferral) |
| `cold_check_answer_shown` | serve_as_ordinary | submit would prime the item and no lapse clears it (a non-routine reveal since the last attempt): the item is served as practice and each due cold task is re-timed to `at + D` |
| `cold_check_assisted` | refuse (submit) | a cold check answered with hints, as a hinted attempt, or declared primed |
| `cold_check_primed` | refuse (submit) | a cold check the ledger primes. Since every serve path asks first, this is reached only when the state changed after the serve, and the message names the change: "a cold retry must be unassisted and unprimed: its answer was shown (tutor answer at …)" |
| `probe_item_answer_shown` | refuse | a probe of an item submit would prime, or one a routine display covers. Unchanged code |
| `quick_check_answer_shown` | refuse | a quick-check offer of an item submit would prime |

**Submit's total is reproduced row for row.** `submit_exposure` gives the same result as `Repository.total_reveal_amount` with submit's arguments, minus the draft's own disclosure:
- the item's rows only;
- a routine display by its coverage (stamped at or after `routine_covered_from(until or at)`), with no upper bound unless the window is bounded;
- every other row after the last attempt (exclusive), or a post-attempt display linked to it in its own second;
- with no attempt, every row.

It sums with `math.fsum` (correctly rounded, like SQLite's compensated `SUM`), so the order rows are read in never moves a total across the threshold. `test_submit_exposure_is_the_sql_total_row_for_row` pins equality with the SQL total on random ledgers, live and bounded. One quirk is kept exactly: submit answers the **first** due task on the item, of any kind, and its cold guard applies only when that task is a cold one (Q42).

## 3. Every path routed

| Path | Old question | Now |
|---|---|---|
| The queue's cold lane (`build_due_queue` → `_defer_revealed_cold_followups`) | non-routine reveals since the task's creation (+ D), and routine coverage. Submit's verdict was not asked | `cold_check_decision`: `serve` keeps the lane; `defer_until` withholds and persists the push; `serve_as_ordinary` withholds the lane, re-times, and keeps the item in the queue as practice (`answer_shown_practice`, no follow-up kind, reason "Practice: you've seen this answer, so its check comes a day after you practise it."). A task re-timed earlier stays offered as practice on every build until an attempt absorbs the exposure. The slate annotation says "practice, not a check" |
| The waiting read (`deferred_cold_followups`, Today's "deferred cold checks") | reveals since creation | the same, plus a task whose item submit would prime (re-timed, served as practice) |
| The plan's pool (`_context` → `_routine_holds` → `cold_check_hold_until`, read-only) | routine coverage only | the decision's `defer_until` (any time-bounded hold); `serve_as_ordinary` is not held |
| Reconcile and serve (`engine._reconcile` displacement) | `cold_check_serve_hold`: routine only | the same function, now the decision: displaced only on `defer_until` (with its reason); re-times persisted |
| The plan's serve (`_held_cold_check`) | routine only | the decision: `defer_until` displaces; `serve_as_ordinary` serves, and the step carries `eligibility` (verdict, reason, message, `check_due_at`) |
| The pick (`select_proposal` → `revalidate_cold_check`) | routine only | the decision, persisted |
| The session serve (`get_practice_item` with a session) and `open_queue_item` | `revalidate_cold_check`: routine only | the decision, persisted, and the detail gains `eligibility` when it is not a plain serve. No cold administration opens, because the task is no longer due |
| The TUI's open (`PracticeScreen.__init__`) | `cold_check_serve_hold`: routine only | the decision, persisted |
| The probe commit and serve (`presentation_commit_payload`, `serve_presentation` → `refuse_routine_display_covered`), the TUI's probe, `get_probe_contract`, the scheduler's slate commit, a precommitted block's members, the causal offer (`_answer_shown`) | routine coverage on the item | `probe_eligibility` (`decide(…, PROBE)`): refused also when submit would prime the item. Same exception and same reason code |
| The placement quick check's offers (`quick_check._candidate_items`) | the serving exclusions: every reveal within one day, routine by coverage | the same exclusions, plus `decide(…, QUICK_CHECK)` for every candidate with ledger rows (the ledger is read once): never an item submit would prime |
| The CLI's attempt | prompted, then validated | BEFORE it prompts: asks `cold_check_serve_decision` (a read), then `validate_attempt_draft` (submit's validation, read-only) as if the decision's re-times were made. A refusal exits 1 with the reason, unprompted, and writes nothing. Otherwise the re-times are persisted (never by a dry run, whose JSON carries the decision) and a cold check served as practice prints the note |
| Submit's auto-prime (`auto_primed_draft`, `reveal_total_for_submission`) | the SQL sum | `submit_exposure`, the same computation (§2) |
| Submit's admissibility (`_resolve_attempt_target`) | `active_followup_task_for_item` plus the guard | `submit_decision` (`decide(…, SUBMIT)`), with the refusal naming its cause |

**What a serve may and may not do.** Anything served as a cold check is accepted as one at submit unless the state changed in between: a new reveal, a hint, a declared prime. The refusal then names the change. Anything served as practice is accepted as practice, because its due cold task was re-timed. A serving hold may be stricter than submit (the learning-object scope, the deferral since creation): that defers, it never refuses.

## 4. The non-routine reveal rule (settled once)

**Kept: submit's rule** (persisted meaning: it decides whether an attempt counts as cold). A non-routine reveal counts from the item's last attempt, without lapse, at or above the 0.35 threshold.

**Serving now agrees with it.** An item submit would prime is never served as a cold check (or a probe, or a quick-check offer).
- **Exposure that time clears** (routine displays only, through `submit_exposure.lapses_at`): the cold check is deferred until it lapses, as before.
- **Exposure only an attempt absorbs:** the item is served as ordinary practice, with an honest label, and each due cold task is re-timed one cold delay later.
  - The practice answer is accepted, recorded primed as submit always recorded it, and absorbs the exposure.
  - The cold check comes back one delay later, cold. On the desktop, that answer's own feedback display then holds it for D + G by the routine rule.
  - If the learner never practises the item, the push repeats once a delay, and the task still ends at its original expiry (`right_censored_expired`): `defer_followup_task` never extends it.
  - It is never left due to walk into a refusal.

**No successor.** The alternative was to let non-routine reveals lapse after D at submit, as routine displays do. That would change which new attempts count as cold, so it would need a successor under the playbook. The case is not strong: a tutor answer is a learner-requested hand-over, not a routine display, and the practice-then-check path already ends the starvation without changing any verdict. Raised as Q36 with the default applied.

**The other serving holds are unified.** Every cold-check serve path now also applies the scheduler's deferral since creation (a non-routine reveal on the item or its learning object, for one cold delay), which round-6 ruling 2 had left to the queue alone. It is time-bounded (at most D), so it cannot starve the plan: the plan waits for a hold that lifts today, or closes, and the next day's plan has the item (§13.3, §14.2). Q37.

## 5. Q33: callers on a past clock

**A bounded window for historical writers.**
- `ApplyAttemptInput.reveal_window_bounded` (default False) is set by `goals.exam_seeding` (the exam's instant), `goals.exam_session` (the sitting's instants at its finish) and `sim.runner` (the simulated day).
- `apply_attempt` threads it through `compute_attempt_application` into `_resolve_attempt_target`, `auto_primed_draft` and `submit_decision`.
- In that window:
  - only reveals stamped at or before the writer's instant count (routine or not);
  - the window starts at the item's last attempt at or before that instant;
  - the cold guard reads the tasks due at that instant.
- `sim.diagnostic_validation` always resets state (§13.6), so it is unchanged.
- Live callers keep their window. A routine row stamped after the clock still covers (round 4's ruling), and a non-routine row after the clock still counts.

**What changes for existing rows: nothing.** Replay never re-derives `primed`: `replay_existing_attempt` reads the recorded flag, and `apply_attempt` skips auto-prime on `replace_existing`. So a rebuild, the shadow, or a replay of an existing attempt under the current label gives the same rows (the parity below is identical). Only new seeded, sitting and simulated attempts get the bounded reading. Before this change, an exam answer seeded on 2026-05-01 for an item whose answer a tutor showed on 2026-05-19 was recorded primed (`test_q33_an_exam_seeded_before_a_later_reveal_is_not_primed` fails on main). The serving reads in a kept-state sim's queue keep ruling 4 (Q39).

## 6. What changes for existing data

- **Schema, labels, references:** none. No migration, no algorithm version, no config key, no RPC name.
- **Replay:** unchanged (§5, §8).
- **`followup_tasks.not_before`** (a WORKFLOW table): a serve may now push a due cold task one cold delay later when its item is served as practice. The push is monotone and never touches the expiry. On the owner's copies, 0 tasks qualify (§8).
- **New attempts:**
  - an exam seeding, an exam sitting or a sim attempt is primed only by reveals up to its instant (§5);
  - a cold check's refusal message has a suffix naming the cause (the prefix tests match on is unchanged);
  - the completion doors validate at the clock they were given (§1). For every live caller that clock is the system clock, so nothing changes; only a caller passing a frozen clock is affected.
- **Serving:**
  - probes and quick-check offers skip items submit would prime;
  - the serve-time cold-check paths also hold for reveals since the task was created (≤ D);
  - an item whose cold check is primed is served as practice.

## 7. Tests

`tests/test_serve_eligibility.py` (427 cases: 400 seeds of the pure property, 8 SQL-parity seeds and 5 real-vault property seeds among them), plus two updated tests.

**Reproduced first.** The new file was run on a `git archive` of `a26284876` with only the new leaf module added (unused by main's code), at `fixtures-local/failfirst/` (pytest's `pythonpath` puts that tree's `src` first). Excluding the pure property and the SQL parity, which test new API: **11 of 17 failed.**
- `test_the_12_9_reproduction_is_served_as_practice_and_accepted`: the plan served `pi_cold`, and submit raised "a cold retry must be unassisted and unprimed" after the answer.
- `test_the_queue_serves_a_cold_retry_submit_would_prime_as_practice`: the lane listed it as `cold_retry`.
- `test_submit_refusal_names_the_change_since_the_serve`: new API (`gather`) on main.
- `test_the_cli_attempt_refuses_an_inadmissible_type_without_prompting`: `Answer []:` was printed.
- `test_the_cli_attempt_refuses_an_assisted_cold_check_without_prompting`: the same.
- `test_the_cli_attempt_records_a_primed_cold_check_as_practice`: exit 1, refused after the answer.
- `test_q33_an_exam_seeded_before_a_later_reveal_is_not_primed`: primed.
- `test_q33_the_bounded_window_also_bounds_the_last_attempt`: new API on main.
- `test_the_real_serve_paths_agree_with_submit`: seeds 1 and 2 failed. The queue served the cold retry primed. Seeds 0, 3 and 4 passed: they drew no reveal before the task.
- The constants test: `attempts`' threshold was a second definition.

The TUI-open, probe-commit, pick and "a refused CLI attempt writes nothing" cases were added after that run, so they have no fail-first record. They exercise the same decision through `cold_check_serve_hold` and `refuse_routine_display_covered`.

**The property and consistency tests.**
- `test_every_serve_agrees_with_submit_at_the_same_instant` (400 seeds, pure): random reveals (routine or not, on the item or a sibling in its learning object, amounts 0.2, 0.4 or 1.0), random tasks of three kinds, an optional last attempt, and a random instant. It checks:
  - after any cold-check decision's re-times, an unassisted submit at that instant is admissible;
  - a serve as the cold check is never one submit would prime;
  - `serve_as_ordinary` happens only when submit would prime with no lapse;
  - `defer_until` is in the future;
  - a probe or quick-check offer is never made on an item submit would prime.
- `test_submit_exposure_is_the_sql_total_row_for_row` (8 seeds): the decision's total equals the SQL total on random ledgers with attempts, live and bounded.
- `test_the_real_serve_paths_agree_with_submit` (5 seeds): a real vault and a real cold task, reveals of both kinds at random moments, and serves at random later moments. It checks:
  - when the queue's cold lane serves the cold retry, submit at that instant is not primed;
  - an unassisted answer after the serve-time decision is never refused.

**Updated, because they pinned main's §12.9 behaviour:**
- `test_ux_phase4_landing.py::test_a_cold_check_on_a_direct_open_is_served_as_on_main_unless_a_routine_display_covers_it` is now `…_is_served_as_practice_when_submit_would_prime_it`. The direct opens of a primed cold retry open no administration and re-time the task; the routine half is unchanged.
- `test_ux_phase4_feedback.py::test_f1l_the_quick_check_never_presents_an_item_inside_routine_display_coverage`: its control (a full tutor answer 24 h 30 min ago, outside the one-day window) is an item submit would prime. It is now excluded (`tutor_answer`), and the control is a glimpse under the threshold (`tutor_answer_glimpse`, amount 0.2, presented first).

## 8. Parity

**The copies.**
- `fixtures/linear_algebra` and `fixtures/probability` (with probability's `.learnloop/state.sqlite`) were copied from the main checkout with `learnloop.db.copies.copy_tree_with_databases`, one copy per side, into `fixtures-local/parity/` (gitignored).
- `arxiv_v2` was not opened.
- Main's code is the archive above, first on `PYTHONPATH`. `LEARNLOOP_CONFIG_DIR` was an empty directory and `LEARNLOOP_AI_PROVIDER` was unset.

| Check | linear_algebra | probability |
|---|---|---|
| open (migrate), main's code and the branch's | 165 → 206 on both; schema hash identical (`bd2d227954163df4`) | 165 → 206 on both; schema hash identical (`ef1b4a046f2e0b3e`) |
| `rebuild --shadow --json` at their own label (mvp-0.8), main vs branch | identical (facet 0, mastery 2, schedule 8; live unchanged) | identical (facet 0, mastery 1, schedule 1; live unchanged) |
| `doctor --json`, main vs branch | 0 differences once the copy's path is normalized (57 issues, 1 error) | 0 differences once the copy's path is normalized (101 issues, 48 errors) |
| reveal ledger rows | 0 | 0 (the vault's database); no `reveal_events` table in `.learnloop/state.sqlite` |
| open cold tasks / due now (2026-10-17T04:09Z) | 1 / 0: a `certification_cold_probe` past its expiry (2026-08-17), not yet swept | 0 / 0 |
| currently-due cold tasks the new rule serves differently | **0** | **0** |

At the one task's own due instant (2026-08-10T06:50Z), both sides serve it as the cold check: no reveal, not primed. So the new rule changes nothing on the owner's vaults today. It would apply when a cold task's item has a non-routine reveal since the item's last attempt, and these vaults have no ledger rows at all.

The scripts and outputs are in `fixtures-local/parity/`: `open.py`, `compare.py`, `count.py` and the `*.json` files.

## 9. Gate

Run on the final code (`f0d3de361`) in the worktree, with `TMPDIR=<worktree>/fixtures-local/tmp`, after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`:

| Check | Result |
|---|---|
| `uv run --no-sync lint-imports --no-cache` | 22 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **12761 passed, 2 xfailed**, 0 failed (16 min 59 s). The 2 xfails are main's strict ones. Main's 12333, plus the 427 new cases and the quick-check test's new control case. An earlier run, on `3c5f0cbca` before the last CLI case was added, gave 12760 passed, 2 xfailed |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **106 passed**, 12657 deselected |
| `validate_vault.py` (architecture vault, after the pipeline map edit) | passed: 1111 notes, every note reachable |
| DB and config references, migration head fixture | not regenerated: no schema, migration or config change |
| CLI help snapshot, RPC pins (`tests/test_mobile_allowlist.py`) | unchanged (both ran in the full suite): no CLI option and no RPC name changed. `get_practice_item` and `open_queue_item` gain an optional `eligibility` key, and only when the decision is not a plain serve |
| frontend (`npm …`), `cargo check` | not run: nothing under `apps/` changed |

Only this record changed after `f0d3de361`. No run had a timing failure.

## 10. Open questions for the owner (defaults applied)

- **Q36 (the rule).** Submit's non-routine rule is kept: such a reveal counts from the item's last attempt and never lapses. Serving agrees by serving the item as practice and re-timing the cold check by one cold delay. The alternative, letting a non-routine reveal lapse after D at submit, would be an algorithm successor (it changes which new attempts count as cold; replay is unaffected). *Default: kept, no successor.*
- **Q37 (holds on every path).** The serve-time cold-check paths (the plan's pool, reconcile and serve, the pick, the session serve, `open_queue_item` and the TUI) now also hold for a non-routine reveal on the item or its learning object since the task was created, for up to one cold delay. That is the queue's own deferral; round-6 ruling 2 had kept it off those paths. It is time-bounded, and the plan waits or closes. *Default: as built (one decision).*
- **Q38 (the label).** The item served as practice is labelled in three places: the queue's reason ("Practice: you've seen this answer, so its check comes a day after you practise it."), the plan step's `eligibility`, and the practice detail's `eligibility`. The desktop renders no new note: it shows the item as ordinary practice, with no cold-check warning, which is true. The queue keeps the item at follow-up priority until it is practised. *Default: no new UI text; a desktop note is a later UX change.*
- **Q39 (Q33's sims).** A kept-state sim's attempts use the bounded window. Its queue builds still read every routine row stamped after the sim's clock as covering (round 4's ruling). *Default: as built.*
- **Q40 (no kill switch).** The serving change removes a refusal loop and adds no persisted meaning, so it has no switch; the only "off" state is the bug. *Default: none.*
- **Q41 (probes and quick checks).** These now also refuse an item submit would prime: any non-routine reveal since its last attempt, at any age. For a never-attempted item, that means any such reveal ever. *Default: as built.*
- **Q42 (submit's quirk).** Submit's cold guard applies only when the first due task on the item, of any kind, is a cold one. This is kept exactly as persisted admissibility, and the decision reproduces it. *Default: unchanged.*
- **Q43 (a stale client).** A queue build that does not persist (`persist_explanations=False`) shows the item as practice without re-timing. A client that submits a cold check without a fresh serve (a stale screen) is still refused, now with the reveal named. Every serve path re-times first. *Default: as built.*
- **Q22 to Q35** stand.
