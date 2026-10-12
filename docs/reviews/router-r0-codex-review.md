# Router R0: Codex review fixes

Branch `router/r0`, worktree `learnanything-router-r0`. Review of the stage at
`cf5d4a06` (codex job `20261012-124408-397ULs`): six findings, three High.
All six reproduced on the original code and are fixed. One more leak of the
same class was found and fixed while fixing F5. No finding was rejected.

Owner decisions in force (2026-10-12): spec defaults accepted, Codex
unrestrained on the subscription, the Decider is
`perplexity/pplx-decider-v1.1-27b` on OpenRouter, frictionless defaults.

## Findings

| ID | Severity | Title | Verdict | Commit | Test (tests/…) |
|---|---|---|---|---|---|
| F1 | High | Attempt-start cutoff includes grading time | Fixed | `0cae9116` | `test_probability_prep.py::test_grading_time_never_moves_the_cutoff_and_an_unknown_start_withholds_history`, `::test_latency_sets_the_cutoff_and_questions_during_the_attempt_never_show` (updated) |
| F2 | High | V3 predictor numbers bypass the start-time filter | Fixed | `0cae9116` | `test_probability_prep.py::test_a_long_latency_moves_the_window_and_the_incumbent_back` |
| F3 | High | V3 substitutes current content for exact historical revisions | Fixed | `0cae9116` | `test_probability_prep.py::test_history_renders_the_verified_revision_never_todays_edit` |
| F4 | Medium | Resume pays again after a committed judgment | Fixed | `0cae9116`, `a993322a` | `test_probability_prep.py::test_resume_recovers_a_committed_verdict_instead_of_paying_again` |
| F5 | Medium | V3 omits required diagnostic evidence | Fixed | `0cae9116` | `test_probability_prep.py::test_rich_state_carries_hypothesis_evidence_and_help_timing_to_both_judges` |
| F6 | Low | The paid readiness command has no dry-run | Fixed | `0cae9116` | `test_probability_cli.py::test_judges_live_check_dry_run_estimates_without_a_key_client_or_receipt` |
| F5a | (found here) | Mutable hypotheses showed today's status and source count | Fixed | `0cae9116` | same F5 test (status `unknown_as_of_this_attempt`, then `durable_active` from transitions) |

`c195b42d` regenerates the DB/config references for the new source anchors
(the renderer now reads six more tables). There is no schema change.

### Reproductions on the original code

Each finding was reproduced on `cf5d4a06` with a scratch test that uses the
original APIs on the Slice 1 diagnosis vault (`tests/diagnosis_split_helpers`).
The vault records pre-grading timing for each attempt: a submission intent one
minute before the graded row, and a 300 s latency. Then the `src/` changes were
reapplied and the new tests were written against the same scenarios.

| ID | What the original code did |
|---|---|
| F1 | att_06 opened 13:54:00, submitted 13:59, graded until 14:00. The cutoff came out at **13:55:00** (`created_at − latency`). An unlinked tutor question at 13:54:30 reached V3. |
| F2 | With att_06 started 3.5 h before submission, reversing the outcomes of the three attempts completed after its start moved V3's incumbent **P(success) from 0.6383 to 0.3617**. V2's window (2 entries) did not change. |
| F3 | att_01 had a pinned exact revision; afterwards its item was edited (new stem, a second criterion). V2 showed `Transpose the matrix M.`. V3 showed **`FUTURE REPLACEMENT STEM`** with `max_points` **8.0** (today's rubric) instead of 4. |
| F4 | Three requests, interrupted once between the judgment commit and the cache rename, then resumed: **4 calls and 4 judgments**. |
| F5 | Hypothesis keys were only `kind, learning_objective, statement, status, validated_evidence_count`. Work entries carried a hint total and no timing. |
| F6 | `learnloop eval judges --live-decider --dry-run` exited **2** (no such option). |

### What changed

**F1. The cutoff uses timing written before grading.** The cutoff is
`submission_intents.created_at − latency_seconds − 2 s`, floored to the second.
The pieces are:

- **The intent.** It is written at the first draft save, or by
  `submit_attempt`'s `_bind_offer` before the grader runs. Either way it is no
  later than the submission.
- **The latency.** It runs from presentation to submission
  (`PracticeScreen.elapsedSeconds`, rounded to whole seconds).
- **The 2 s margin.** It covers that rounding and the IPC hop.

`practice_attempts.created_at` is stamped after grading
(`_compute_resolved_grade_application`), so it never sets a cutoff. Without both
an intent and a latency the start is unknown. Then V2 and V3 show no history at
all and carry `history_withheld`, which names the reason. The incumbent folds
nothing, so its numbers are the frozen priors (`observations_before_start: 0`).

The old fallback, one second after the previous submission, is removed. It
inferred a start from a completion time, and background or exam grading can
finish after the next item opens. A cutoff from an intent recorded at an early
draft save, or before a restart, only moves the cutoff earlier, which hides
more.

Known limit: the sidecar is serial. A submit with no earlier draft save that
queues behind a long request could stamp its intent a few seconds after the
click. The margin covers rounding and IPC, not a long queue. Teach-back binds
no submission id, so its attempts never get a start.

**F2. The incumbent is fitted only on observations before the start.**
`prediction_points(..., start_of=renderer.cutoff)` walks the time-ordered stream
once and reads the incumbent at each prediction's own prefix (observations
strictly before the cutoff). The harness past still keys the cache, as it
should. The test checks the whole V2 and V3 states, predictor numbers and region
statuses included, and asserts they don't change when the forbidden outcomes are
reversed. It also asserts that the harness-past fold does change, so the test is
sensitive.

**F3. History follows the harness's revision policy.** The renderer receives the
harness rows (`inputs["attempts"]`):

- **`exact` rows** render the verified snapshot. They use the rubric frozen in
  the grade's single assessment contract for max points and failed criteria.
- **`reconstructed_current` rows** (the explicit `--legacy-fallback
  current_content`) render today's content with a `revision_note` that says so.
- **Every other prior attempt** is omitted from V3 and counted in
  `omitted.unverified_revision`. This covers `excluded` rows, rows with no
  harness row, and exact rows whose snapshot or contract can't be verified.
  Nothing falls back to today's content.

`_item` no longer falls back to today's content for an exact row whose snapshot
fails verification. It renders `(item text unavailable)`.

**F4. A resumed run recovers committed verdicts.**

- `committed_judgments` reads the valid `llm_probability` verdicts from
  `judgment_ledger`, keyed by the full request identity: judge, question-set
  version, route settings hash (which covers the model), request digest, state
  hash and state version. The rationale now also records `requested_model`.
- Before paying, `prepare_judge` writes the checkpoint for every uncached
  request with a committed verdict (`recovered_from: judgment_ledger`). A dry run
  counts these as `recoverable` and leaves them out of the estimate.
- The test interrupts at each persistence boundary:
  - **after the commit, before the checkpoint:** no new call;
  - **before the commit:** the answer was never durable, so that one request is
    asked again, and its receipt shows both calls;
  - **after the checkpoint:** zero calls.

**F5. The hypothesis evidence and help timing now reach both judges.** Each
hypothesis carries:

- **`source_attempt`**: its card ref, days before, LO and first-divergence
  quotes.
- **`evidence_for`**: the diagnosing attempt, plus later non-passes on its LO or
  target facets, with quotes.
- **`evidence_against`**: later passes there.
- **Bounded lists**: at most 4 references each, with full totals.
- **`repairs_tried`**: cold successes and failures as of the cutoff.
- **`cause_scope`** and **`written_days_before`**.

All of it is read from the same verified, pre-cutoff attempts the card shows.
Work entries keep the hint total and gain `tutor_questions_during` (seconds into
the attempt, hints used before, type). Questions point back with
`attempt_ref`. Ordinary hint timing isn't persisted anywhere: the
`interaction_events` kinds and the session checkpoint hold no hint times. The
card says so in `not_recorded` instead of implying zero. The test renders the
plan, sends it through both judges' fakes, and asserts that the exact card
reached the Decider's `state` and the LLM's prompt.

**F5a (found while fixing F5). Mutable hypothesis rows no longer leak today's
state.** Misconceptions and unresolved factors are mutable. Before the fix their
`status` was today's, and `validated_evidence_count` counted today's sources. A
misconception resolved after the predicted attempt showed as resolved.

- **Misconceptions** now take their as-of status from
  `misconception_transition_events` before the cutoff.
- **Other cases:** a row last written at or after the cutoff is labelled
  `unknown_as_of_this_attempt`.
- **The count** is replaced by the as-of evidence totals.

**F6. The readiness check has a dry run.** `learnloop eval judges --live-decider
--dry-run` resolves the route, the request body and the caps. It prints the
token and cost estimate without loading `settings.env`, building an
authenticated client or writing a receipt. `--dry-run` without `--live-decider`
is refused, because readiness alone sends nothing.

The state version moves to `llm-probability-state-v2`, so no cache or verdict
from the old renderer can be reused.

## Consequence for the owner's comparison

On the worktree's tracked `linear_algebra` backup copy
(`fixtures-local/r0-linear_algebra`), aggregate counts show:

- **The attempts:** 70 attempts from 2026-07-22 to 07-28; 11 have a latency, 30
  have a submission id, and **0 have an intent**. Submission intents arrived
  later, with migration 161.
- **The dry run:** it now reports `history.start_established = 0` of 53
  predictions. V2 and V3 carry no history on that copy.
- **The estimate:** 111 requests per judge (Decider 69,896 tokens, $0.0014; LLM
  483,202 tokens, subscription). It was 143, because states with withheld
  history collapse.

The V1–V3 comparison is informative only on attempts recorded since intents
existed. Read `history.start_established` in your live vault's dry run before
paying.

## Paid calls in this step

None. The fixes and tests use fakes only. The one earlier authorized live
Decider call ($0.00000588, recorded in `router-r0.md` §1) was not repeated. The
dry runs above make no requests.

## Gate

The gate ran on `a993322a` (the code at this review's commit; the review
files are docs only). The full suite and the durability lane ran under
`flock /tmp/learnloop-fullsuite.lock`.

| Check | Result |
|---|---|
| `uv sync --extra dev`, `uv pip install pypdfium2` | OK (the stage does not touch `learnloop_mobile`) |
| `uv run lint-imports --no-cache` | **10 contracts kept, 0 broken** |
| `uv run pytest -n auto` | **7,166 passed**, 14 existing warnings (Python 3.12 fork and sqlite datetime-adapter deprecations), exit 0 |
| `uv run pytest -m durability` | **66 passed**, 7,100 deselected, exit 0 |
| Targeted: `test_probability_{prep,cli,arms}`, `test_judge_routes`, `test_decider_client`, `test_cli_help_snapshot`, `test_sqlite_file_copies` | 92 passed |
| Frontend | Not changed; not run |
| `db_generate_reference.py` / `db_validate_reference.py` | No schema change (head stays 169). The references were regenerated for the new source anchors; the validator reports **0 errors** (266 table notes, 31 config section notes) |
| `validate_vault.py` | Passed (1,029 notes) |

The CLI help snapshot (`tests/cli_help_snapshot.json`) was regenerated. Only
the `eval judges` entry changed, for the new `--dry-run`.

## Open questions for the owner

1. **Restrict the paired comparisons to predictions with an established start?**
   With history withheld, V2 and V3 add nothing over V1 at those positions. That
   dilutes V3 vs V2 on older vaults. The dry run reports the count; filtering the
   report would be a small change to `evaluate(pairwise=...)`.
2. **Record hint reveal times?** Ordinary hints keep only a per-attempt total.
   A reveal event would give V3 (and the router card, §4 "hints and their
   timing") real timing. Out of scope here (no schema change in this step).
