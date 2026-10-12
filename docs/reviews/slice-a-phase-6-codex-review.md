# Slice A Phase 6: Codex review fixes

**Branch:** `slice-a/phase-6` (worktree `learnanything-phase-6`). Not merged, not
pushed. **Review:** Codex job `20261012-124549-Lo3dNt`, ten findings (F1-F10).
**Fix commit:** `2884cee0`. Owner decisions in force: 2026-10-12 (spec
defaults accepted; frictionless defaults; live behind kill switches). Every
change below acts only at `mvp-0.10` with `placement.enabled = true`; the kill
switch still restores `mvp-0.9` exactly (G9 tests unchanged and passing).

## Review

### Method

Each finding was reproduced on the unfixed code first (`a83ef5ac` plus the new
tests), with the real scheduler, attempt, reveal-ledger, reservation and
placement code on fresh test vaults, then fixed, with a regression test that
fails on the old code:

| Finding | Reproduced on the unfixed code |
|---|---|
| F1 | After a passed check on `lo_diag`, the queue served `pi_diag_easy`, `pi_diag_hard` and `pi_diag_mid` again |
| F2 | Fast-track due 2026-06-02T12:03Z; the queue at minute 4 served `pi_diag_hard`, `pi_diag_mid`; an answer at minute 8 resolved the check as `passed` |
| F3 | `production_admissibility` returned `post_reveal_not_independent` (reveal on a sibling item) while placement marked the check `passed` (`primed=0`, `hints=0`) |
| F4 | With the conditional-gain favourite `pi_diag_mid` reserved for an exam, routine serving excluded it and the quick check presented it |
| F5 | Answers at minutes 20 and 21 (check started at minute 1, 8-minute budget) produced a `quick_check` assumption |
| F6 | `placement_self_report` had no session identity and never touched `session_checkpoints` |
| F7 | A failure injected at `insert_quick_check` left an active calibration session; the retry failed with "already has an active calibration session" |
| F8 | After a passed check, "I don't know this" returned `status=learning` with `assumption_id=None`; `returned_learning_object_ids` held the LO, the serving override was empty |
| F9 | Three "I know this" / "I don't know this" toggles on a three-item LO reported 27.0 minutes saved |
| F10 | Six self-reports left `judgment_ledger` at 0 rows |

### Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Passing the first review restores the skipped learning items | fixed | `2884cee0` | `test_assumed_known.py::test_a_passed_check_keeps_the_remaining_learning_items_withheld` |
| F2 | High | Fast-tracked topics can complete their "14-day check" immediately | fixed | `2884cee0` | `test_assumed_known.py::test_fast_track_check_waits_for_its_review_interval`, `::test_an_early_miss_still_returns_the_lo_to_learning` |
| F3 | High | A non-independent answer can pass the assumed-known check | fixed | `2884cee0` | `test_assumed_known.py::test_a_post_reveal_answer_cannot_pass_the_check`, `::test_a_post_reveal_answer_never_counts_toward_fast_track` |
| F4 | High | Quick checks expose held-out exam items | fixed | `2884cee0` | `test_quick_check.py::test_quick_check_never_presents_an_item_routine_serving_excludes[reserved\|held\|owned]` |
| F5 | Medium | Expired quick checks absorb unrelated later practice | fixed | `2884cee0` | `test_quick_check.py::test_an_abandoned_check_ignores_later_practice_in_the_same_session`, `::test_only_presented_answers_count_and_k_is_enforced_server_side` |
| F6 | Medium | "I know this" leaves a resumable draft for the skipped item | fixed | `2884cee0` | `test_placement_sidecar.py::test_i_know_this_on_a_card_clears_that_cards_durable_draft`, `::test_a_self_report_keeps_a_draft_for_another_card`; vitest `PracticeScreen.test.tsx`, `PlacementControls.test.tsx` |
| F7 | Medium | Interrupted quick-check creation leaves an orphan calibration session | fixed | `2884cee0` | `test_quick_check.py::test_interrupted_creation_leaves_no_orphan_and_a_retry_recovers_the_check`, `test_placement_sidecar.py::test_quick_check_rpc_retry_with_the_same_request_id_returns_the_same_check` |
| F8 | Medium | An unlinked "I don't know this" return does not affect learning admission | fixed | `2884cee0` | `test_assumed_known.py::test_i_dont_know_this_after_a_pass_returns_the_lo_to_learning`, `::test_i_dont_know_this_on_a_practised_unassumed_lo_admits_its_new_items`, `test_placement_sidecar.py::test_placement_state_carries_the_current_intent` |
| F9 | Medium | Report 3 counts temporary deferrals repeatedly as saved learning | fixed | `2884cee0` | `test_placement_report.py::test_report3_counts_each_learning_obligation_once` (and the updated `::test_report3_scores_first_reviews_by_source`) |
| F10 | Medium | Learner placement verdicts bypass `judgment_ledger` | fixed | `2884cee0` | `test_assumed_known.py::test_learner_placement_verdicts_append_to_the_judgment_ledger`, `::test_a_failed_ledger_append_rolls_back_the_receipt` |

Ten fixed, none rejected. Four High findings fixed.

### What changed

**Placement intent (F1, F8; `placement/state.py`).** Each LO's routing is now
derived in time order from its decisions, returns and answers
(`LearningObjectIntent`, never stored):

- `assumed` while an assumption is open;
- `maintenance` after a passed check, until a later miss on the LO (any
  answer the learner did not answer cleanly) or "I don't know this";
- `learning` after a missed check, a miss in maintenance, or "I don't know
  this", with or without an open assumption, until a later explicit "I know
  this" (a new decision) supersedes it.

The scheduler withholds a maintained LO's never-attempted items (its practised
items keep their normal reviews) and admits a `learning` LO's never-attempted
items as new material. "I know this" on a maintained LO decides nothing new
(status `maintenance`); "I don't know this" there returns it to learning.
`placement status`, the RPC LO state and the inspector carry `intent` and
`intent_reason`; the inspector labels maintenance and offers "I don't know
this" on it.

**The review interval (F2; `scheduling/scheduler.py`, `placement/state.py`).**
An open assumption now holds the LO's whole long first interval: no item of it
(never-attempted or practised) is served routinely until `first_review_due`,
and then only the chosen check item. Learner-requested cards stay the explicit
exception. Resolution separates the qualifying check from repetitions:

- a clean answer before the due date is **early practice**: recorded
  (`Assumption.early_answers`, report 3's `early_practice_answers`), never the
  check;
- a miss (partial marks, hints, priming, "don't know", assistance), early or
  on schedule, still returns the LO to learning quietly (the spec's "a failure
  quietly returns it"; report 3 counts it under `resolved_early` when early);
- from the due date on, the first clean answer the independence rule admits
  passes the check.

**Independence (F3; `placement/rules.py`, `placement/state.py`).** Placement
calls the existing rule rather than a copy: `evaluate_independence` asks
`attempts.reveal_ledger.production_admissibility` over the window ending at the
answer, and a final coldness receipt for the attempt must pass its
`unassisted` and `answer_leakage` dimensions (the field's strict rule).
`AnswerFacts` gains `independent`, `independence_reason`, `reveal_event_id` and
`independence_since`; an answer whose independence was not evaluated is never
clean (fail-closed). Windows:

- fast-track and quick-check answers: since the item's previous attempt
  (any reveal on the item or its LO before a first attempt counts);
- the check: since the later of the item's previous attempt and the decision,
  so exposure before the decision (at least the review interval old) does not
  veto every future check, while a reveal after it does.

A clean answer the rule rejects is `ineligible` at the check (neither pass nor
miss; `Assumption.ineligible_answers`) and `not_independent` for fast-track and
the quick check (never counts; the quick check decides `learning`). Fast-track
receipts store each answer's independence facts (G8 replay unchanged).
`RULES_VERSION` is `placement-rules-v2`. One import-linter exemption is added,
`placement.state -> attempts.reveal_ledger`, with the same justification as the
existing `tutor.tutor_qa -> attempts.reveal_ledger` one: the package graph
already runs attempts -> substrate -> placement, and reveal_ledger imports only
`clock` and `db.repositories` at module level.

**Quick checks (F4, F5, F7; `diagnosis/quick_check.py`, `placement/decisions.py`,
migration 170).**

- `scheduling/serving_exclusions.py` is the one place routine serving reads
  exam reservations, pending-variant holds and staged-controller ownership.
  `build_due_queue` (no behaviour change) and the quick check's candidate
  selector both use it.
- Each served item is a persisted presentation (`placement_quick_check_items`,
  WORKFLOW): at most k per check. An answer is bound to a presentation only if
  it is the first attempt on that item in the check's practice session, at or
  after the presentation and no later than the check's boundary (its budget's
  end, or its stop/expiry if earlier). Only bound answers are results; k is
  enforced on presentations server-side. An outstanding presentation stays the
  target while its LO is undecided and its item still servable.
- The calibration session and the quick-check row are created in one
  `Repository.atomic()` transaction. `start_quick_check` takes a `request_id`
  (unique, `placement_quick_checks.request_id`); a retry with it, or a repeat
  start over the same scope while that check is active, returns the existing
  check. The desktop sends a fresh UUID per start.

**The skipped card's draft (F6).** `placement_self_report` accepts
`sessionId`; with `practiceItemId` it clears that session's checkpoint only if
it still points at that card (`Repository.clear_practice_checkpoint_for_item`),
inside the report's own transaction. The practice card passes its session.

**Report 3 (F9; `placement/report.py`, `placement-report-3-v2`).** Savings are
defined over unique learning obligations (an active item on a decided LO that
was not practised before the LO's first decision), each counted once and read
from the LO's current intent: `items_avoided` (never practised, LO in
maintenance: the only "saved" minutes), `items_deferred_pending_check`
(provisional, reported separately), `items_deferred_then_returned`,
`items_deferred_then_learned` and `items_used_as_checks`. The saving and the
provisional deferral are subsets of `learning_obligations_estimate`. On the
reproduction the toggles now report 0 minutes saved; one open "I know this"
reports 9 provisional minutes; after the check passes, 6 saved; after one of
the two items is practised, 3.

**The verdict ledger (F10).** Every learner self-report ("I know this", "too
easy", including the retirement path, and "I don't know this") appends an
owner verdict to `judgment_ledger` in the receipt's transaction: task
`placement_override`, `left_kind = learning_object`, `judge = owner`, verdict =
the report, rationale = provenance (trigger, status, algorithm and rules
versions, and the linked receipt `{table, id}`), input hash over all of it.
Each new verdict on an LO supersedes the previous one, so the ledger's head is
the learner's current stated intent. A failed append rolls the receipt back.
Fast-track and quick-check decisions are rule receipts, not verdicts, and stay
out of the ledger.

### Not changed (outside the numbered findings)

The review's conformance table also lists: no quick check on the import
result, quick-check ordering by `conditional_gain` under the incumbent, no
`reveal_events` at the quick check's end, and D6's `q = 0.8`. These are not
numbered findings: the stage records them as deviations 1, 2 and 4 and open
questions 2 and 4 in `slice-a-phase-6.md` (the incumbent's `conditional_gain`
is its plain per-LO information, as described there). They are left for the
owner's checkpoint rather than widening this fix step.

### Migration

`170_placement_quick_check_presentations.sql`: `placement_quick_checks.request_id`
(unique when set) and `placement_quick_check_items` (WORKFLOW, classified in
`table_roles.py`; no DERIVED table, no replayer). Head fixture
`fixtures/migration_head_169` renamed to `migration_head_170`: a backup-API copy
upgraded through 170, `journal_mode=DELETE`, integrity ok, FK-clean, no WAL
companions; README and the five hard-coded paths (three tests, two reference
scripts; `SCHEMA_HEAD = 170`) updated. Main already has 169-171, so this
branch's 169 and 170 will be renumbered at merge.

### Paid calls and manual runs

No paid call, no model route, $0.00. Manual check (read-only) on the stage's
backup-API copy `fixtures-local/phase6-probability`: `placement status` shows
the one open self-report as intent `assumed` (0 early, 0 ineligible answers);
report 3 v2 now reports its 5 withheld items as 15.0 provisional minutes and
0.0 saved (v1 had called them 15 minutes saved), over 192.0 minutes of 64
learning obligations. No tracked working vault was read or written.

### Gate

Run on the fix commit `2884cee0`.

| Check | Result |
|---|---|
| `uv sync --extra dev`, then `uv pip install pypdfium2` | OK (`uv sync` removes `pypdfium2`; reinstalled 5.14.0). The stage does not touch `learnloop_mobile` |
| `uv run lint-imports --no-cache` | **10 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7,147 passed**, 0 failed, 14 existing warnings (Python 3.12 fork and SQLite datetime-adapter deprecations); 200 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **67 passed**, 7,080 deselected; 41 s |
| `npm install` (apps/learnloop-tauri) | OK (existing notice: esbuild's postinstall blocked by allowScripts); lockfile unchanged |
| `npm run typecheck` | **0 errors** (`tsc --noEmit` exit 0) |
| `npm test` (vitest) | **74 passed** in 18 files |
| `db_generate_reference.py` / `db_validate_reference.py` | Schema **170**, **270** table notes, **0 errors** |
| Head fixture | `migration_head_170`: `journal_mode=delete`, integrity ok, FK-clean, `max(version)=170`, no WAL companions |
| Tracked working vaults | Untouched (`git status` clean for `fixtures/linear_algebra`, `probability`, `arxiv_v2`) |

The placement suites alone (`test_assumed_known.py`, `test_quick_check.py`,
`test_placement_report.py`, `test_placement_sidecar.py`,
`test_placement_signals.py`, `test_placement_upgrade.py`,
`test_placement_fixture_copies.py`) run 70 tests outside the durability lane
(plus the placement durability test inside it), 20 of them new for this review.
