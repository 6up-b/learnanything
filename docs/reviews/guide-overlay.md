# Guide overlay fix: the Reader Guide reads the diagnoser's statement

**Checkpoint:** branch `fix/guide-overlay` (worktree
`learnanything-guide-fix`, base `main` at `19798a0c`). Owner-directed
2026-10-12 ("launch the guide fix now"). This is a display-only change, so it
needs no algorithm successor, no migration and no config change; the
defaults fingerprint is untouched, so no snapshot was recomputed. There is no
frontend change. Nothing was merged or pushed. The reader workbench spec's
RW3a (`spec_reader_workbench_v1.md` §3.4 item 1, §6.2, G30) builds on this
fix.

Commits:
- `a18639b2`: fail-first tests;
- `c6d5a6ae`: the fix;
- the commit after it: this review file.

## The defect

`reader_guidance._learner_signal` read
`Repository.active_errors_by_learning_object`, which selects raw
`error_events`. Since Slice 1 M2 (blind grading plus the history-aware
diagnoser, `mvp-0.10` and later), a blind-graded attempt's events store only
the grader's localization:
- `misconception_statement` is NULL;
- `is_misconception` is the taxonomy prior
  (`attempts/blind_grading.py:506`, `:553`).

The diagnoser's statement and verdict (`diagnosis/split/live.py:279`) are laid
over the events on read by `error_events_for_attempt`. On split vaults the
Guide therefore fell back to the error type. Reproduced before the fix, on a
test split vault at `mvp-0.10` and at `mvp-0.14`:

> Revisit this to resolve: conceptual schema error.

It should have named the diagnoser's statement.

## Part 1: the fix

- **One repository helper.**
  `Repository.active_errors_by_learning_object_overlaid(lo_id)`
  (`db/repositories.py:1977`) is the per-LO counterpart of
  `error_events_for_attempt`.
  - It reads the same rows in the same order and fetches the live views of
    their attempts in one query. `DiagnosisStoreMixin.live_causal_views` now
    takes optional `attempt_ids`; without them it behaves as before.
  - It applies the existing `merge_causal_view_into_events`, so no overlay
    logic is duplicated.
  - Only the view's keys change (`_EVENT_VIEW_KEYS`,
    `db/stores/diagnoses.py:22`), and of those `ActiveErrorEvent` carries
    `misconception_statement` and `is_misconception`.
  - Grader-owned fields are unchanged: id, error type, severity, timestamps
    and `misconception_id`.
  - These events are returned exactly as stored:
    - joint-graded events;
    - events whose diagnosis is pending, failed or superseded (the same
      "in force" rule as every other overlay);
    - events with no attempt.

  The raw method is unchanged. Its docstring now says serving and replay read
  it, and display reads the overlaid one. The helper is reusable as is for
  RW3a's margin cues.
- **The Guide** (`reader/reader_guidance.py:142`) reads the overlaid helper.
  The reason names the diagnoser's statement. The ranking does not change,
  because the boost uses `severity` and `created_at`, both grader-owned.
- **The TUI feedback screen** (`tui/screens/feedback.py:533`) had the same
  defect (Part 2), and it is fixed the same way. The screen renders the error
  attributions with the grade and only then runs the inline diagnosis
  (`_run_inline_diagnosis`). Reading the overlay alone would therefore change
  nothing in the normal flow, so the attributions are re-rendered once the
  diagnosis is `done`. The pill now shows the diagnoser's misconception
  verdict.

**The Guide writes no evidence and serves nothing (confirmed).**
- `build_guide_plan` calls only repository getters: the extraction run,
  revision, artifact, IR, golden-path runs, reviewed placements, reader
  interaction events, authored questions, mastery and the overlaid errors.
- Its only caller, `learnloop_sidecar/handlers/reader.py:418`
  (`reader.guide_plan`), wraps it without writing anything.
- Questions are still opened only by `reader.present_question`.
- `test_guide_plan_writes_nothing` snapshots every table of a diagnosed split
  vault before and after a plan is built, and they are equal.
- The TUI change only re-renders a widget.

### Tests (fakes only)

The fail-first commit `a18639b2` fails 3 tests in `test_reader_guidance.py`
and 5 in `test_active_errors_overlay.py`. All pass at `c6d5a6ae`.

| Test | What it pins |
|---|---|
| `test_reader_guidance.py::test_split_guide_reason_names_the_diagnosers_statement[mvp-0.10, mvp-0.14]` | **Fail-first.** Real blind grade, diagnosis drained with the M1 fake (statement added): the reason names the diagnoser's statement, not the error type, and the raw row is still empty |
| `…::test_split_guide_falls_back_to_the_error_type_while_the_diagnosis_is_pending` | Pending diagnosis: the reason is the error type, with no crash and no diagnoser call |
| `…::test_split_guide_falls_back_to_the_error_type_when_the_diagnosis_failed` | Failed diagnosis (`max_attempts = 1`): same fallback |
| `…::test_joint_guide_plan_is_unchanged_by_the_overlay_read` | **mvp-0.9 parity**, with a shadow diagnosis run too: the overlaid read equals the raw read, and the whole plan is byte-identical (`json.dumps(sort_keys=True)`) to the plan built with the raw read patched back in |
| `…::test_guide_plan_writes_nothing` | Display only: every table is unchanged by a plan build |
| `test_active_errors_overlay.py` (4 repository tests) | The diagnoser's statement and verdict, grader-owned fields kept, raw rows unchanged; a `transient_execution` diagnosis clears the taxonomy prior's `is_misconception`; pending and attempt-less events pass through; overlaid equals raw on every LO of a joint vault |
| `test_active_errors_overlay.py` (2 TUI tests) | **Fail-first.** The attributions are re-rendered with the statement and the `misconception` pill after the inline diagnosis; nothing is re-rendered when no diagnosis is needed |

## Part 2: audit of the other `active_errors_by_learning_object` callers

Fields the overlay can change: `misconception_statement` and
`is_misconception`. It also changes `causal_class`, `registry_match` and the
`repair_plan` causes, but `ActiveErrorEvent` does not carry those. A caller
is defective under the split only if it reads one of the first two.

| Caller | Reads | Effect | Defective under split? | Action |
|---|---|---|---|---|
| `tui/screens/feedback.py:527` (now `:533`) `_error_content` | `misconception_statement`, `is_misconception`, `error_type`, `severity` | Display only | **Yes**: the label is the error type and the pill shows the taxonomy prior | **Fixed** (above) |
| `attempts/attempts.py:3075` `_auto_resolve_clean_error_events` | `id`, `created_at` | Persisted: resolves `error_events` (RAW_LEDGER) and is replayed | **No**: reads no overlay field | Unchanged; it must stay raw for replay |
| `attempts/attempts.py:3123` `load_attempt_prior_state` → `AttemptPriorState.active_errors` | Only consumer: `compute_surprise` (`:3476`) → `predicted_error_type_distribution` (`attempts/surprise.py:137`), which reads `error_type`, `severity`, `created_at` (`:149`) | Persisted: `attempt_surprise` (DERIVED, replayed) | **No**: reads no overlay field | Unchanged |
| `goals/exam_session.py:72` `_predicted_correctness_for_item` | `ability_vector` (`scheduling/selection_rewards.py:270`) reads `is_misconception` into `misconception_posterior_by_error_type` (`:282`–`:285`) | Persisted: frozen exam predictions | **No in effect.** The posterior differs under the split (`{conceptual_schema_error: 1.0}` raw vs `{}` overlaid when the diagnoser says `transient_execution`). But `predicted_correctness_from_vectors` (`:460`) reads only mastery and facet values, so the frozen prediction is identical | Unchanged |
| `diagnosis/probes.py:206` `build_hypothesis_set`, legacy raw-event lane | `is_misconception` (`:207`), `misconception_id` (`:209`), `error_type`, `severity`, `created_at` | **Serving.** The live consumer is the follow-up misconception-discrimination gate: `followups.py:1816` builds the set, and `expected_information_gain` (`:1519`) turns it into the misconception EIG added to each candidate's `rank_score`. `enter_probe` (`probes.py:272`, which persists to `hypothesis_sets`, COMPAT) has no production caller; only tests call it | **Yes** (see below) | **Not changed.** Raise with the owner |

### `probes.py:206` under the split (serving, not changed)

The legacy lane admits an unlinked event (`misconception_id IS NULL`) as an
error-type hypothesis `misconception:<error_type>` when `is_misconception` is
true. Under a joint grade that flag is the grader's verdict. Under the split
it is the taxonomy prior (`blind_grading.py:506`). The diagnoser's verdict
(`live.py:279`) lives only in the overlay, so the lane ignores the diagnoser.

**Observed** with a scratch script (not committed) on the test split vault
(`mvp-0.10`, real blind grade, M1 fakes), for `lo_svd_compute`:

| Diagnoser `causal_class` | Raw `is_misconception` | Overlaid | Hypothesis labels while pending | After the diagnosis |
|---|---|---|---|---|
| `transient_execution` | True (prior for `conceptual_schema_error`) | **False** | `mastered`, `misconception:conceptual_schema_error`, `unfamiliar` | **unchanged: the misconception hypothesis stays** |
| `learner_state` | True | True | same | same |

**Failing scenario A.**
1. A learner makes a copying slip on an SVD item. The blind grader localizes
   it as `conceptual_schema_error`, and the taxonomy prior is True.
2. The diagnoser rules it a `transient_execution` slip.
3. On the next follow-up decision for that LO with an active registry belief,
   the gate's hypothesis set (`followups.py:1816`) still gives prior mass to
   `misconception:conceptual_schema_error`. That changes the normalization of
   the misconception EIG (`followups.py:1519`), and so how candidates rank.

Under a joint grade, the grader's `is_misconception=False` would have kept it
out. The owner wants follow-ups chosen by EIG/EVSI. With this defect, the EIG
is computed over a hypothesis the diagnoser has already rejected.

**Failing scenario B (by inspection, not reproduced).** The fakes always grade
`conceptual_slip`, so this case was not run.
1. The blind grader localizes `retrieval_failure` or `local_slip` (prior
   False).
2. The diagnoser says `learner_state` and writes a misconception statement.
3. The holding-pen candidate does not promote, so `misconception_id` stays
   NULL.
4. The lane skips the event. Under a joint grade it would have entered as an
   error-type hypothesis.

**What a fix needs.** This changes serving and a persisted record, so per
`docs/algorithm-change-playbook.md` it takes the next free `mvp-0.N` successor
at its merge. That means:
- read `is_misconception` through the overlay
  (`active_errors_by_learning_object_overlaid` already provides it) only for
  vaults at or after the successor;
- decide what a **pending** diagnosis means for the lane: keep the prior, as
  today, or hold the event out until it is diagnosed;
- test parity for joint and earlier split vaults;
- extend the follow-up decision tests. Follow-up decisions are logged, so
  history keeps the ranking it had when written.

The same applies to the neighbour lane `_neighbor_misconceptions`
(`probes.py:1468`), which reads `active_error_events()` with the same
`is_misconception` gate.

### Adjacent raw readers (not in the brief; recorded, not changed)

These read `Repository.active_error_events()` (all LOs, raw), not the per-LO
method:
- **Scheduler**, `scheduling/scheduler.py:183`. It feeds `ability_vector`, whose
  `misconception_posterior_by_error_type` uses the raw `is_misconception`. That
  value is logged only, in the `decision_features.ability_vector_json` receipt
  (`scheduler.py:953`); no ranking term reads it. Under the split the logged
  feature reflects the taxonomy prior, not the diagnoser. It matters only if a
  learned router later trains on that column. `_repair_value` and
  `_recent_error` read only grader-owned fields.
- **CLI `learnloop misconceptions`**, `cli/app.py:2072`. This is display. By
  default it lists events whose raw `is_misconception` is true, so under the
  split it lists by taxonomy prior. A one-line fix needs an all-LO overlaid
  read. It was left alone because its `--json` output is labelled stable, and
  changing what `is_misconception` means there is the owner's call.
- **`ops/doctor.py:1143`.** Reads `error_type` only. Not affected.

## Notes

- **Statement shown regardless of verdict.** The Guide names the statement
  whenever one exists, as it always has under joint grades, even when the
  diagnoser's `causal_class` is not `learner_state` (`is_misconception`
  False). Gating it on the verdict would change joint rendering, so it was not
  done.
- **Double full stop (pre-existing, cosmetic).** The reason template is
  `f"Revisit this to resolve: {detail}."`, so a statement that ends in a full
  stop renders `"…applies.."`. Joint vaults have always shown this; the M1 fake
  grader's statement ends in a full stop. It was left alone because joint
  vaults must render byte-identically. RW3a's fixed wording templates are the
  natural place to fix it.
- **Superseded diagnosis.** After a blind regrade, nothing is in force until
  the new diagnosis completes (the existing overlay rule), so the Guide shows
  the error type in that window. This matches every other overlay reader.

## Paid calls

None. Everything ran on fakes; no copy of an owner vault was made or needed.

## Gate

Run at `c6d5a6ae`; the review commit is documentation only.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 14 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | 8544 passed, 0 failed, 0 skipped (216 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | 93 passed, 8451 deselected, 0 failed (85 s) |
| Frontend | not changed: not run |
| DB reference scripts | schema not changed: not run |

## Open questions for the owner

1. **Probe hypothesis lane under the split** (`probes.py:206`, `:1468`):
   should it read the diagnoser's verdict? This is a serving change and needs
   a successor. If yes, what should a pending diagnosis do: keep the prior or
   hold the event out?
2. **`learnloop misconceptions`**: should the CLI list by the diagnoser's
   verdict on split vaults? This is display, but its `--json` is labelled
   stable.
3. **The `decision_features` receipt** logs a taxonomy-prior misconception
   posterior on split vaults. Should it, before a learned router trains on it?
