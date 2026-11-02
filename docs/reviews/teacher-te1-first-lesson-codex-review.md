# Teacher TE1 (with curriculum C4): Codex review fixes

**Stage:** `teacher-te1-first-lesson`, branch `teacher/te1-first-lesson` (worktree `learnanything-astrafix`). **Review:**
codex-job `20261101-212931-l6Trib` (gpt-6.1-sol), 13 findings (4 High, 9 Medium) and six "claims that don't hold".
**Base of this step:** `2de4f7317c`. **No paid or live call was made**: every model is a fake (`tests/teacher_fakes.py`,
plus `MeteredTeacher` in the new test file, which routes each request through the real `ai.execution.model_call` seam
so the request gate admits it). No migration, no config key, no schema change. No owner vault, `~/.config/learnloop`,
`settings.env` or `~/.codex` was read; nothing ran against `fixtures/linear_algebra`, `fixtures/probability` or
`fixtures/arxiv_v2`. The desktop catalog was regenerated under `env -i` (`scratchpad/te1/iso.sh`). Two ad-hoc
`uv run python` probes ran outside `env -i`: they imported only pure string functions
(`tutor.tutor_qa.span_answer_overlap`, `teacher.delayed.question_overlap`) on literal strings, with no vault, config,
key or network.

**Reproduced first.** Every finding has a test in `tests/test_teacher_te1_review_fixes.py`. With `src/` checked out at
the base `2de4f7317c` (tests at this step), all 23 tests written for the findings failed (`23 failed`); with the fixes
they pass. The three new `LessonScreen` vitest cases failed against the base screen (`3 failed | 5 passed`) and pass
now. One more test (F9's read recovery) was added after that run for a refinement of the fix.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | The per-lesson spending cap does not bound requests | fixed | `232fe29911` | `test_f1_a_second_request_in_one_action_is_refused_when_it_would_pass_the_cap`, `test_f1_the_inline_grader_is_inside_the_lesson_envelope`, `test_f1_a_graded_check_spends_from_the_lesson_envelope` |
| F2 | High | Held grades train future evidence weights | fixed | `a27561ff43` | `test_f2_a_held_cold_grade_resolves_nothing_until_released` (hold by regrade, release by adjudication) |
| F3 | High | Plan statements and recaps bypass output guards | fixed | `232fe29911` | `test_f3_a_key_in_a_plan_statement_or_a_recap_is_withheld`, `test_f3_every_displayed_field_writes_reveal_rows` |
| F4 | High | Resumed lessons resend material that has become protected | fixed | `232fe29911` | `test_f4_a_passage_held_out_after_delivery_is_never_resent_or_read_back`, `test_f4_a_revoked_alias_cannot_be_cited` |
| F5 | Medium | Pool inversion compares probabilities for different questions | fixed | `a27561ff43` | `test_f5_the_pool_inverts_on_the_committed_cold_item_not_the_check`, `test_f5_a_forecast_agreeing_with_the_cold_prediction_leaves_the_mass_near_the_learned_one` (the review's numeric probe) |
| F6 | Medium | The weight likelihood does not reproduce the actual mastery trajectory | fixed | `a27561ff43` | `test_f6_the_trajectory_at_the_recorded_mass_reproduces_the_outcomes_recorded_prior` |
| F7 | Medium | Delayed checks can reuse material shown in the lesson | fixed | `232fe29911` | `test_f7_a_vault_question_reused_as_a_check_is_never_the_cold_check`, `test_f7_a_sibling_of_a_shown_item_is_never_the_cold_check` |
| F8 | Medium | A downstream prerequisite edge is treated as proof of transfer | fixed | `232fe29911` | `test_f8_a_downstream_edge_alone_is_not_transfer`, `test_f8_a_downstream_item_whose_rubric_measures_a_taught_facet_is_transfer` |
| F9 | Medium | Accepted turns are not recoverable across interrupted execution | fixed | `232fe29911`, `df3db91008` | `test_f9_an_accepted_check_turn_interrupted_before_its_effects_recovers_on_reload`, `test_f9_closing_is_one_transaction_and_an_interrupted_close_recovers`, `test_f9_an_interrupted_turns_reads_run_with_the_next_action_never_in_lesson_view` |
| F10 | Medium | Deferred read results are discarded before successful delivery | fixed | `232fe29911` | `test_f10_deferred_read_results_are_kept_until_a_turn_consumes_them` |
| F11 | Medium | Opening failures leave the desktop with no retryable lesson | fixed | `232fe29911` (backend), `d58b47159d` (screen) | `test_f11_an_opening_failure_carries_the_saved_lesson_and_resume_runs_it`, `test_f11_the_sidecar_error_carries_the_lesson_id`; vitest `LessonScreen.test.tsx` (3 new cases) |
| F12 | Medium | Provider schema failures bypass contract correction | fixed | `232fe29911` | `test_f12_three_provider_invalid_outputs_close_the_lesson_as_a_contract_failure` |
| F13 | Medium | Check-correctness forecasts have no outcome resolver | fixed | `a27561ff43` | `test_f13_lesson_forecasts_have_resolvers`, `test_f13_a_withdrawn_check_censors_its_forecast` |
| C-derived | claim | DERIVED tables reproduce live state row for row | fixed | `b273936274` | `test_the_derived_state_rebuild_reproduces_the_live_tables_exactly` (now compares all three tables, and again after a later cold outcome) |

No finding was rejected.

## What changed, per finding

- **F1 (spend, §17).** One durable envelope per lesson: every `lesson.turn` action runs under a
  `MeteredRequestGate` subclass (`service._lesson_spend`) installed with `ai.execution.gate_model_requests`, so every
  physical metered request of the action (the teacher's, the inline blind grader's, a retrieval call's, a provider's
  repair or retry) is reserved before it is sent against what the lesson already spent (input at ~4 chars a token plus
  the route's output budget `ai.output_budget`, at `teacher.metered_price_per_million`) and settled into a durable
  `spend` ledger row (`spent_before_usd` of the next action reads them). A refused admission closes the lesson
  `budget` (in the teaching loop and when the grader is refused). Usage rows are now written in a `finally` (an
  exception no longer skips them). The receipt's `cost` is the whole lesson's (every action's calls and tokens,
  `metered_usd`, `cap_usd`). Subscription routes are never limited (Slice A §5 rule 6); an unknown price with a cap set
  fails closed (the spend framework's rule).
- **F2 (held grades).** `held_grades.held_for_review_attempts` (the canonical predicate) now filters
  `qualifying_outcomes`, the calibration answers and the resolvable checks; a released grade qualifies again on the
  next replay.
- **F3 (guards).** `_displayed` lists every learner-facing field (message, choices, prediction, check, plan
  statements, recap); each passes `check_all` (the posed check's own fields exempt from its own solution guard, as
  before), and all displayed text is accounted as reveal rows, in the same transaction as the accepted turn.
- **F4 (protection).** `revalidate_material` runs before every teacher call: `brief.passage_teachable` recomputes
  `SourceBook.revoked` against the section library NOW, and brief probe items now withheld are collected. The prompt
  redacts revoked passages and withheld stems everywhere (brief, results, transcript) and drops earlier teacher turns
  that cited a revoked alias; `read_source` refuses a revoked alias (and now also withholds an alias whose text gives
  the open check's solution away); the citation guard and the anchor contract treat a revoked alias as undelivered.
  Aliases keep their numbers (never reused).
- **F5 (pool, §12.2).** `checks.cold_reference` names the committed cold item (the delayed retention picker's choice
  as of now, the lesson's own and shown items and their lineage excluded; the LO's parameters when none fits) and its
  horizon (`delayed.due_days`). `p_A` and `pool_implied_mass` are both computed for that item at that horizon (drift
  included); at λ = 0 the mass is exactly §12.1's. The retained forecast records the LO state it was made from, and the
  pool learns from `p_A` recomputed for the resolving item at the outcome's horizon (`forecast_p_a`). The pool's
  forecaster is the family recorded with the forecast.
- **F6 (likelihood, §12.1).** `recorded_trajectory` reads, for the check and every later update on its LO before the
  outcome, the attempt step's recorded observation weight (`attempt_debug_payloads.observation_weight`: coverage,
  grading reliability, hints, error sharpening, familiarity discount) and recovers each update's interpretation noise
  from its recorded variance step (`attempt_surprise.posterior_delta`); `trajectory_state` re-applies them through
  `learner.mastery.update_mastery` with only the check's weight scaled by `σ(η)/m₀` (the weight is linear in the
  attempt's mass). At the recorded mass it reproduces the outcome's recorded prior state to 1e-6 (tested, with two
  intervening updates, one hinted). An attempt with no record falls back to the first-order form, named on the trace
  (`likelihood`, `intervening`). The prequential fixed-0.5 comparison uses the same recomputation.
- **F7 (fresh delayed checks, §13).** `delayed.shown_vault_items` finds the vault items whose question the lesson's
  displayed text reproduces (share of the question's word pairs, numbers kept, at the house auto-prime threshold); they
  and their lineage (`family_id`, contrast pair, shared stimulus, source exercise) are excluded from retention and
  transfer, and recorded on the receipt (`exposure.shown_items`).
- **F8 (transfer, §13).** A downstream item qualifies only when a criterion of its rubric measures a landed LO's facet
  (criterion targets, else the item's facets, against the LOs' blueprint facets); a goal item only when its recorded
  presentation (`evidence_fingerprint.representation`) differs from every shown item's and every check already
  picked. Otherwise transfer is reported unavailable with a warning. (Fixture: three items gained a presentation.)
- **F9 (recovery, §7/§18).** An accepted turn, its delivered results and its reveal rows are one transaction; each
  effect is marked (`refs.turn`, `refs.effect`) in the transaction that makes it (plan + its entry, receipt + its entry,
  withdraw + its entry), and `turn_executed` ends the turn. `recover` re-runs unmarked effects idempotently (a re-posed
  check rewrites the same item id): the next action runs it under its spend envelope, and `lesson.view` (no model call)
  runs everything but read actions. Closing (delayed checks, receipt, row, close entry) is one transaction.
- **F10 (deferred results).** `results_delivered` is written with the accepted turn that consumed them (same
  transaction), so an outage keeps them pending; once delivered they stay in the transcript.
- **F11 (desktop recovery).** `LessonError.details.lesson_id` once the lesson is saved, passed to the sidecar error;
  a new `lesson.turn` action `resume` runs the teacher's turn an outage interrupted (no-op when nothing waits). The
  screen keeps a "Try again" on an outage: it resumes a saved lesson (showing what it holds) or repeats an opening that
  saved nothing; after "Use OpenRouter instead" the learner presses it.
- **F12 (schema failures).** `AIInvalidOutput` (and `AIOutputTruncated`) from `execute_structured_operation` is a
  correctable `schema` refusal counted by the three-consecutive rule.
- **F13 (resolvers).** The shared forecast report resolves `lesson_check_correct` on the check's own attempt under its
  current grade (withdrawn: censored; held: held; ungraded: pending; never answered in a closed lesson: censored) and
  `lesson_step_retained` on the first qualifying cold outcome (the same reader the pool learns from); both score the
  binary event `success` (full credit, the lesson's own "right").
- **DERIVED claim.** The live writer and the replayer both replay through the latest answered check
  (`tables_through`), so they agree row for row whatever happened since; every reader of the current posterior replays
  the ledgers itself.

## Not addressed here (outside the findings)

- The planted-recovery claim (τ support and the interaction priors' `simulation` basis): no test tells the τ points
  apart yet; left for the landing/TE2 report work.
- Spec-conformance gaps the review listed that no finding covers: compaction, the turn's `visual`, uncited source
  claims, the Today entry and practice-now close offer, the adopted §11 couplings. Unchanged.
- The pool-implied mass still inverts a simplified check observation (full reliability) at check time: the check's
  observation factors are only known after the attempt step runs.
- `module_validate.py` reports 1336 issues on this tree before and after (the Python module reference is stale
  repo-wide); not part of this gate.

## Gate (this step)

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 38 kept, 0 broken |
| targeted pytest (`-n 6`, memory-capped), 23 files below | **643 passed, 1 xfailed** |
| `--durable-sqlite` on `test_teacher_te1_review_fixes.py`, `test_teacher_te1_weight.py`, `test_teacher_te1_migration.py` | 44 passed |
| `npm install`; `npm run typecheck` | ok |
| `npx vitest run --maxWorkers=4 src/screens/LessonScreen.test.tsx` | 8 passed |
| `npm run frontend:build` | ok |
| `desktop_generate.py` / `desktop_validate.py` (under `env -i`) | regenerated; 303/303 TS + 6/6 Rust, ACTIVE=309, reproducible |
| cargo check | not run (nothing under `src-tauri` changed) |
| DB reference generate/validate | not run (no schema change) |

Targeted pytest files: `tests/test_teacher_te1_review_fixes.py`, `tests/test_teacher_te1_lesson.py`,
`tests/test_teacher_te1_weight.py`, `tests/test_teacher_te1_curriculum_c4.py`, `tests/test_teacher_te1_migration.py`,
`tests/test_teacher_te1_successor.py`, `tests/test_architecture.py`, `tests/test_forecast_receipts.py`,
`tests/test_cold_retry_reschedule.py`, `tests/test_mobile_allowlist.py`, `tests/test_notes_never_read.py`,
`tests/test_rebuild_orchestrator.py`, `tests/test_regrade_contract_successor.py`, `tests/test_registry_audit.py`,
`tests/test_desktop_rpc_contract.py`, `tests/test_sidecar_registry.py`, `tests/test_table_roles.py`,
`tests/test_rebuild_equivalence_review.py`, `tests/test_held_grade_evidence.py`, `tests/test_tracked_fixture_databases.py`,
`tests/test_teacher_te0_review_fixes.py`, `tests/test_teacher_te0_fix_round2.py`,
`tests/test_teacher_te0_confidence_events.py`.

The full suite, the whole durability lane and the whole vitest run are the landing gate's (owner rule 2026-10-17).

## Files touched

`src/learnloop/teacher/service.py`, `src/learnloop/teacher/checks.py`, `src/learnloop/teacher/delayed.py`,
`src/learnloop/teacher/brief.py`, `src/learnloop/teacher/guards.py`, `src/learnloop/teacher/actions.py`,
`src/learnloop/learner/lesson_weight.py`, `src/learnloop/evsi_calibration/forecast_report.py`,
`src/learnloop_sidecar/handlers/lesson.py`, `apps/learnloop-tauri/src/screens/LessonScreen.tsx`,
`apps/learnloop-tauri/src/api/dto.ts`, `tests/test_teacher_te1_review_fixes.py` (new), `tests/teacher_fakes.py`,
`tests/test_teacher_te1_weight.py`, `apps/learnloop-tauri/src/screens/LessonScreen.test.tsx`,
`docs/specs/spec_teacher_v1.md` (§20 as-built), `docs/reviews/teacher-te1-first-lesson.md` (pointers), the desktop
catalog under `docs/learnloop-architecture-vault/Reference/Desktop/`.

## Re-review (codex-job `20261101-222330-VW72um`, verdict REOPENED)

**Base of this step:** `f0a9b75985`. F2 and F3 were confirmed fixed. F1 and F4 were reopened; F14 and F15 are new
(Medium). **No paid or live call was made**: every model is a fake (`TeacherFake`, `MeteredTeacher`); no ad-hoc
Python or CLI ran outside pytest. No migration, no config key, no schema change, no frontend or `src-tauri` change
(the desktop catalog is unaffected: no RPC or DTO changed). No owner vault, `~/.config/learnloop`, `settings.env` or
`~/.codex` was read.

**Reproduced first.** The seven re-review tests were committed alone (`b9b49979f7`) and run against the base `src/`:
6 failed, 1 passed (the passing one, `test_rr_f4_nothing_revoked_leaves_the_prompt_unchanged`, pins that the F4 fix
changes nothing when nothing is protected). Each failure was the finding's own: F1, no `spend_reserved` row at send
time and, after a crash between send and settlement, the next request admitted past the cap (`view["closed"]` was
false); F4, the passage sentence present in the next prompt through the saved plan, and through an uncited message,
the open check and the open prediction; F14, resume made no call (`3 == 3 + 1` failed); F15, the resumed call ran
with `help_reply = False`. With the fixes (`6ba1484ec2`) all seven pass.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Reservations live only in memory; a crash after sending forgets them | fixed | `6ba1484ec2` | `test_rr_f1_a_reservation_is_durable_before_the_request_and_outlives_a_crash`, `test_rr_f1_a_settled_request_replaces_its_reservation` |
| F2 | High | Held grades train future evidence weights | confirmed fixed | `a27561ff43` | (re-review probe) |
| F3 | High | Plan statements and recaps bypass output guards | confirmed fixed | `232fe29911` | (re-review probe) |
| F4 | High | Saved plan, open check, prediction and uncited copies still resend protected text | fixed | `6ba1484ec2` | `test_rr_f4_a_saved_plan_copying_a_now_held_out_passage_is_not_resent`, `test_rr_f4_an_uncited_copy_open_check_and_prediction_are_not_resent`, `test_rr_f4_nothing_revoked_leaves_the_prompt_unchanged` |
| F14 | Medium | Resume silently skips a failed read follow-up | fixed | `6ba1484ec2` | `test_rr_f14_resume_runs_a_read_follow_up_an_outage_interrupted` |
| F15 | Medium | Resume loses the pending help mode | fixed | `6ba1484ec2` | `test_rr_f15_resume_keeps_the_pending_help_mode` |

No finding was rejected.

### What changed

- **F1.** `LessonSpendGate.admit` commits a `spend_reserved` ledger row (reservation id, estimate, purpose, provider,
  tokens) before it returns the admission, so the reservation is on disk before the request is sent; if that write
  fails, the in-memory reservation is released and the request is not sent. `settle` writes the `spend` row with the
  reservation id. `_spent_usd` (the envelope's starting total and the receipt's `metered_usd`) is the settled rows
  plus every reservation no settlement replaced, at its whole estimate: the gate's own rule for a request that
  reported nothing. No lesson model request runs inside a ledger transaction (the teacher call, the grader and the
  read actions all run outside `repository.atomic()`), so each reservation commits as written.
- **F4.** Before every call `_prompt` scrubs the whole context it resends (brief, open check, open prediction, plan,
  results, transcript: the teacher's turns, the learner's replies, the grader's feedback) against the text that became
  protected since it was saved: each sentence of every revoked passage and every now-withheld brief stem. A string
  that reproduces one, by the tutor's span filter (`span_leaks_expected`, the measure that withholds a retrieved span
  before the tutor sees it; its thresholds are the existing `keep` guardrails, no new constant), is replaced whole by
  the withdrawal notice. Nothing protected leaves the prompt byte-identical. The earlier structural redaction (aliases,
  stems, cited turns) stays. Like the guards it is lexical: a paraphrase is not caught (the review's probes were
  copies).
- **F14 and F15.** `resume` reads the call it owes from the ledger (`_pending_call`): a learner's or code's step with no
  accepted teacher turn after it, in the help mode the learner's reply recorded (F15); or the action's first accepted
  turn whose reads ran with no accepted turn after it (F14), whose non-deferred read results ride with the resumed call
  as they did with the original; that call counts as the action's second, so its own reads are deferred (the
  one-further-call bound). The pending state is the ledger itself, so it survives a restart and clears only when the
  consuming teacher turn commits.

### Gate (this step)

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 38 kept, 0 broken |
| targeted pytest (`-n 6`, memory-capped), 20 files below | **564 passed** |
| `--durable-sqlite` on `test_teacher_te1_review_fixes.py`, `test_teacher_te1_lesson.py` | 48 passed |
| npm / vitest / frontend build / cargo check | not run (no frontend or `src-tauri` change) |
| DB reference generate/validate | not run (no schema change) |

Targeted pytest files: `tests/test_teacher_te1_review_fixes.py`, `tests/test_teacher_te1_lesson.py`,
`tests/test_teacher_te1_weight.py`, `tests/test_teacher_te1_curriculum_c4.py`, `tests/test_teacher_te1_migration.py`,
`tests/test_teacher_te1_successor.py`, `tests/test_notes_never_read.py`, `tests/test_architecture.py`,
`tests/test_forecast_receipts.py`, `tests/test_mobile_allowlist.py`, `tests/test_rebuild_orchestrator.py`,
`tests/test_registry_audit.py`, `tests/test_desktop_rpc_contract.py`, `tests/test_sidecar_registry.py`,
`tests/test_table_roles.py`, `tests/test_held_grade_evidence.py`, `tests/test_tracked_fixture_databases.py`,
`tests/test_teacher_te0_review_fixes.py`, `tests/test_teacher_te0_fix_round2.py`,
`tests/test_teacher_te0_confidence_events.py`. The full suite, the whole durability lane and the whole vitest run are
the landing gate's (owner rule 2026-10-17).

### Files touched

`src/learnloop/teacher/service.py`, `tests/test_teacher_te1_review_fixes.py`, `docs/specs/spec_teacher_v1.md` (§20
as-built), this file.
