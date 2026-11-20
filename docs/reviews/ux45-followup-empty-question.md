# UX-45: re-ask an incomplete follow-up author once

Status: fixed in the working tree of `fix/ux45-followup-empty-question`, not yet committed or landed.
The step 0 below was recorded before production or test edits.
Base: `0b1fcf13da`, branch `fix/ux45-followup-empty-question`.

## Measurement supplied by the walk

A first-day learner's third answer met two criteria and missed two. Diagnosis took
32 seconds; one `followup_probe_authoring` operation took 12 seconds and 330 output
tokens. Its `FollowupProbeAuthored` had `prompt_md = ""`, a 636-character key,
a 24-character suffix, and empty criteria, predictions, intended manipulations,
held-constant and incidental-change lists. `empty_question_or_key` failed the
workflow, queued a need one hour later, and showed “Couldn't prepare a question
on this. It's noted for later.” Other same-day answers omitted create IDs and a
whole topic list: compliance cannot be assumed. No private answer was inspected.

## Step 0 (before code)

Read `followup_run/authoring.py` whole, admission and jobs, the follow-up spec
`spec_followup_generate_serve_v1.md`, the build record `followup-fg1.md`, the wire
model/prompt, follow-up tests/helpers, identity pins and CLAUDE.md's identity rule.
Searching reviews for the literal `followup_probe_authoring` found no build-record
hit; the spec identifies `followup-fg1.md`, whose “Measured with fakes” describes
one author call, two after transport failure, zero on unreadable protection.
`ux43-empty-build.md` is absent on this tip. UX-42's record and plan provider now
include the validation failure in the JSON repair request only.

The prompt says “Write that one question: a fresh question whose answer tells
these causes apart.” It says “`expected_answer_md` is the full correct answer”,
“`criteria` are 2 to 4 independently gradable facts”, and “`predictions` has one
entry per hypothesis”. There is no permission to omit the question. Optional
instructions are “`measurement_pattern`, when present” and “`avoid_phrases`, when
present”; neither makes authoring optional. The question's wire field is named
only by the schema, while the prose calls it “the question”: a possible weakness,
not evidence of the measured model's reasoning; this patch preserves that text.

`build_context` supplies topic title/concept/summary, hypotheses, router decision,
facets, measurement pattern, source question, existing prompts and avoid phrases.
It supplies no attempt count, prior-follow-up requirement or learner answer.
Summary can be blank after protection filtering; source question can be None;
existing prompts and avoid phrases may be empty. Hypotheses may have empty scope
or statement and a null target reference; this lane still requires concrete rival
causes. A first-day learner's sparse history does not instruct an empty answer.
The actual prompt/context was not supplied, so this is a code-path inspection,
not a claim about its exact values in the walk.

The wire schema requires three strings (`prompt_md`, `expected_answer_md`,
`surface_suffix`) but no minimum length; all five top-level lists default empty.
Nested IDs/descriptions/axes are unrestricted strings, points are integers,
and prediction `fails_criteria` defaults empty. Empty manipulation lists alone
are not rejected by `check_output`; do not invent a new check for this defect.
Minimum string/list lengths would alter the schema sent to the provider and its
identity; they are unnecessary here and will not be added. CLAUDE.md requires
keeping compared bytes or deliberately bumping; this task permits no pin move.

### Every rejection and today's outcome

The exact re-ask group will be defined once, as a reason-to-requirement mapping:

| Ignored output contract | Existing check |
|---|---|
| `empty_question_or_key` | stripped question or key empty |
| `criteria_contract_invalid` | fewer than two criteria, blank/duplicate IDs, or nonpositive points |
| `prediction_names_unknown_hypothesis` | unknown hypothesis reference |
| `prediction_not_over_the_criteria` | empty failure set or unknown criterion IDs |
| `a_hypothesis_has_no_prediction` | predictions do not cover the reference set |
| `manipulation_contract_invalid` | undeclared-author axis, or changed axis also held constant |

| Unusable/disallowed content (no new re-ask) | Existing check/treatment |
|---|---|
| `prompt_equals_key` | question is its own answer; fail |
| `predictions_do_not_discriminate` | rival failure sets identical; fail |
| `repeats_protected_material` | reproduces a protected non-reserved item; fail |
| `protection_unavailable` | withheld/reserved material cannot be read; fail closed, potentially before any call |
| `cause_matches_reserved_question` | context rejection; normal job precheck takes practice lane with zero calls |
| `question_matches_reserved_question` | constant in authoring, raised by admission, not check_output; existing one job retry then practice lane |

Output rejections become `AdmissionFailed`; jobs fail the workflow, release held
feedback, log generation_failed, and deduplicate a factor need with not_before
one hour later. No bad item is served. An early protection failure goes straight
to fail_workflow (before factor attachment); a need is queued only if the workflow
has a factor. Reserved matches have the distinct existing treatment above.

### Intended rule, request and time bounds

Use the existing generation job's second lease for one contract correction,
immediately queued, with a workflow event carrying the first rejection and the
remaining deadline. Second request text states the failed requirement; original
prompt/schema and successful-first rows stay identical. Same checks run again.
Second failure follows today's path. Contract, transport/crash and reserved-echo
retries share `MAX_GENERATION_ATTEMPTS = 2`, rather than multiplying their limits.
A workflow therefore makes at most two authoring operations; no intervention and
protection refusals can make zero. Provider-internal HTTP retries/JSON repair are
separate physical requests and already bounded by their provider's policy/deadline.
Specifically, the tool-free plan route allows three sends per `_send` and one
JSON repair, at most six HTTP attempts per structured operation, hence at most
12 across the existing two job attempts. This upper bound is unchanged. The
measured wire-valid empty answer invokes no JSON repair: normally one send before
this fix, two sends if its one corrective answer is needed after this fix.

The step uses the resolved client's profile timeout (normally inherited from
`ai.timeout_seconds`, default 180 seconds). The worker lease is 900 seconds, not
a learner timeout. `diagnosis.next_item_wait_seconds` defaults to 10 seconds but
`serving._diagnosis_timed_out` explicitly applies only while diagnosis is pending:
“generation has *Continue without it*.” A contract re-ask will share the original
authoring timeout, subtracting elapsed time and queue delay. No fresh timeout for
the correction. If time is exhausted, keep today's failure and one-hour background
need; do not increase the learner's wait. The generation worker remains the only
caller; no serving/config change is needed. Deadline tests must cover residual
budget and a correction whose queued budget has expired.


## Implementation and judgment calls to read first

The sole contract-retry allowlist is `authoring.CONTRACT_REASK_REQUIREMENTS`:
six existing rejection reasons, each mapped to the corrective sentence. No
validator is weakened or added. Empty manipulation lists and an empty suffix
are still governed by the existing checks; this fix does not silently strengthen
the wire contract. Equal question/key and indistinguishable predictions remain
content failures, rather than requests to fill missing structure.

`request_authored_probe` appends the reason and requirement after the original
prompt only on correction. It uses the original `FollowupProbeAuthored` schema.
`admission.author_probe` runs the same context/protection and output checks on
each answer. First-request prompt and schema bytes, versions and identities do
not move. There is no configuration, migration, algorithm tag or serving change.

`jobs._run_probe_lane` uses the existing second job attempt, not an inner loop.
On the first contract rejection it appends a pending-to-pending
`authoring_contract_retry` event containing `rejection_reason`, `deadline`,
`rejected_attempt` and `retry_attempt`, then requeues immediately. Both operations
run under the same `followup_generation` receipt owner/job ID and store their own
input and answer. On correction the input receipt itself states the first reason.
The first receipt may say successful transport: it records the valid wire answer;
the workflow event records its subsequent local rejection.

The second attempt reads the durable event, so a process restart does not lose
its reason or give it a fresh time allowance. The retry has the original profile
budget minus elapsed time, context preparation and queue delay, computed at the
request boundary. A correction with less than one second left is not sent (chat
transports floor at one second), and the original reason follows today's failure
path. The 900-second job lease and 10-second diagnosis-only Next timeout are not
misrepresented as authoring deadlines. The plan provider honors the supplied
remaining total timeout across its own HTTP retries and JSON repair. No ingest
background-model scope is entered by this worker.

Judgment: the two-attempt cap is shared with existing transient/crash and reserved
question retries. A transport retry followed by an incomplete answer has spent
its second attempt and fails; an incomplete answer followed by transport failure
also fails after two operations. A correction does not grant a third operation.
Reserved-question content keeps its existing retry/practice-lane behavior within
that shared cap; “no new re-ask” does not remove its pre-existing retry. Unrelated
entry, lesson and factor-need generation paths keep their existing job handling;
this correction targets the learner's follow-up workflow. A failed workflow's
one-hour factor need remains a separate, deduplicated background job.

The learner sees the existing Preparing line during the correction and retains
Continue without it. A good correction is admitted, pinned and opened through
the existing serve door, which burns its single-use identity. A second bad answer,
a disallowed-content answer, or exhausted authoring time releases feedback,
shows the existing couldn't-prepare/noted-for-later line, and lets Next continue.
Cancellation between attempts cancels the queued correction. No new UI text is
introduced. Real latency, delivery and model recovery remain unmeasured.

## Fail-first evidence

All tests use the existing `AuthorFake`, `StructuredClientFake`, rival-causes vault
and sidecar journey helpers. The measured fake preserves the supplied shape:
empty question, key length 636, suffix length 24 and all five lists empty.

Initial new file on unchanged production: **9 failed, 2 passed in 3.31s**. One
failure deliberately captured successful-first stable row columns. With those
expected bytes set, still before production edits: **8 failed, 3 passed in 2.80s**.
These failures show one call rather than two, or done/failed rather than queued
for correction. The content-failure, good-first and already-spent transport retry
controls correctly pass before the fix; they are preservation tests, not fabricated
failures.

The expanded file added both prediction-reference contract reasons and a complete
row snapshot. Restoring the three production files from `git show HEAD:<file>`
without touching the index, running the tests, then restoring working bytes in
`finally` gave **11 failed, 2 passed in 2.83s** (one captures the complete snapshot).
The final unchanged-production check gave **13 failed, 4 passed in 3.14s**.
All 13 behavior regressions fail before the fix; the four controls are a good first
answer, nondiscriminating content, a transport retry already spent, and an initial
answer that consumed its entire time budget. The final fixed file gives
**17 passed in 3.21s**.

The successful-first case repeats the setup and admission expectations from
`test_a_miss_with_two_rivals_generates_one_pinned_probe`. It holds the expected
workflow/event/job values and also SHA-256 of every column of every row in
`followup_workflows`, `followup_workflow_events`, `followup_generation_jobs`,
`generated_probe_items` and `causal_probe_candidates`, with existing helpers
freezing generated ULIDs and wall time. The unchanged-code digest is
`b947645765b753e735a59b8b21fd29cc57acfe5272fddae59c412280335db94e`;
the fixed code produces exactly those bytes. No existing golden was edited.

## Verification commands

`t.sh` and `py.sh` mean the supplied isolated wrappers. All pytest invocations
name explicit files, use at most two workers and never select the whole suite.
The final baseline recheck used `py.sh python` to temporarily restore the three
production files, run the same test command and restore edits in `finally`.
Earlier editing/capture helpers likewise touched only the working files, never
the index. Temporary logs and runner scripts live outside tracked files.

| Command | Result |
|---|---|
| `t.sh tests/test_followup_authoring_retry.py -q -n 2` (initial baseline capture) | 9 failed, 2 passed in 3.31s |
| Same, baseline row columns pinned, before production edits | 8 failed, 3 passed in 2.80s |
| `t.sh tests/test_followup_authoring_retry.py tests/test_followup_generate_e2e.py tests/test_identity_pins.py -q -n 2` | 368 passed in 16.88s |
| `t.sh tests/test_followup_authoring_retry.py -q -n 2` (expanded unchanged-production capture) | 11 failed, 2 passed in 2.83s |
| Same, final fixed file | 17 passed in 3.21s |
| Same, final unchanged-production recheck via `py.sh python` | 13 failed, 4 passed in 3.14s |
| `git diff --check` | exit 0, no output |


The filename selection contains **60 files**. The first 40-file chunk completed;
the second 20-file chunk encountered fixture/test stalls. No interrupted run's
partial progress is counted as verified. The interrupted commands were:

```sh
t.sh tests/test_hint_feedback_widening.py tests/test_mobile_v2_feedback.py tests/test_mobile_v2_followup.py tests/test_reader_followup_valuation.py tests/test_reader_followups.py tests/test_reader_followups_rereview.py tests/test_reader_followups_review.py tests/test_reader_followups_round3.py tests/test_reader_followups_round4.py tests/test_reader_followups_round5.py tests/test_reader_followups_round6.py tests/test_reader_followups_round7.py tests/test_reader_followups_round8.py tests/test_reader_followups_successor.py tests/test_source_retrieval_followup.py tests/test_t6_followup_composition.py tests/test_t6_followup_rereview.py tests/test_t6_followup_review.py tests/test_tui_feedback.py tests/test_ux_phase4_feedback.py -q -n 2 -m 'not arc_close'
# Interrupted (exit 130) after stalled progress; no complete pytest result.

t.sh tests/test_hint_feedback_widening.py tests/test_mobile_v2_feedback.py tests/test_mobile_v2_followup.py tests/test_reader_followup_valuation.py tests/test_reader_followups.py tests/test_reader_followups_rereview.py tests/test_reader_followups_review.py tests/test_reader_followups_round3.py tests/test_reader_followups_round4.py tests/test_reader_followups_round5.py tests/test_reader_followups_round6.py tests/test_reader_followups_round7.py tests/test_reader_followups_round8.py tests/test_reader_followups_successor.py tests/test_source_retrieval_followup.py tests/test_t6_followup_composition.py tests/test_t6_followup_rereview.py tests/test_t6_followup_review.py tests/test_ux_phase4_feedback.py -q -n 2 -m 'not arc_close'
# Interrupted (exit 130) after stalled progress; no complete pytest result.

t.sh tests/test_hint_feedback_widening.py tests/test_mobile_v2_feedback.py tests/test_mobile_v2_followup.py tests/test_reader_followup_valuation.py tests/test_reader_followups.py tests/test_reader_followups_rereview.py tests/test_reader_followups_review.py tests/test_reader_followups_round3.py tests/test_reader_followups_round4.py tests/test_reader_followups_round5.py tests/test_reader_followups_round6.py tests/test_reader_followups_round7.py tests/test_reader_followups_round8.py tests/test_reader_followups_successor.py tests/test_source_retrieval_followup.py tests/test_t6_followup_composition.py tests/test_t6_followup_rereview.py tests/test_t6_followup_review.py tests/test_ux_phase4_feedback.py -q -n 2 -m 'not arc_close' -k 'not test_f1k_the_tui_open_defers_a_cold_check_a_routine_display_covers'
# Interrupted (exit 130) after stalled progress; no complete pytest result.

```

A diagnostic rerun used `-vv -o faulthandler_timeout=30` and a 120-second
runner deadline. It identified the remaining mobile fixture stall. A separate
bounded TUI run identified its shutdown stall. The following is the complete
completed/timeout command transcript, including the final reduced selections.
The runner invokes argument arrays; multiword `-k` expressions are quoted here
for a reproducible shell spelling. The layout and architecture files each ran
alone, with no other pytest process active.

```sh
t.sh tests/test_curriculum_c1_round5_followups.py tests/test_e0_review_round4_followup.py tests/test_followup_authoring_retry.py tests/test_followup_codex_review.py tests/test_followup_diagnostic_selection.py tests/test_followup_fg1c_codex_review.py tests/test_followup_fg1c_r1_exposure_independence.py tests/test_followup_fg1d_panel_read.py tests/test_followup_fg1d_probe_shadow.py tests/test_followup_generate_e2e.py tests/test_followup_journey.py tests/test_followup_live_shape.py tests/test_followup_migration.py tests/test_followup_next_matrix.py tests/test_followup_reserved_only.py tests/test_followup_rival_factor.py tests/test_followup_router.py tests/test_followup_single_use.py tests/test_followup_successor.py tests/test_followup_workflow.py tests/test_followups.py tests/test_followups_batch5_c5_ledger.py tests/test_followups_batch5_lesson.py tests/test_followups_batch5_recap_dependencies.py tests/test_followups_batch5_recap_protection.py tests/test_followups_batch6_power_probe_cache.py tests/test_followups_batch6_prefetch_decided_once.py tests/test_followups_batch6_prefetch_next_section.py tests/test_followups_batch6_prefetch_plan_wait.py tests/test_followups_batch6_review_fixes.py tests/test_followups_batch6_router_report.py tests/test_followups_batch6_te1b_card.py tests/test_followups_batch6_verify_fixes.py tests/test_followups_batch7_note_titles.py tests/test_followups_batch7_prefetch_capped_resume.py tests/test_followups_batch7_prefetch_link_served.py tests/test_followups_nov2_figure_provenance.py tests/test_followups_nov2_help_fold.py tests/test_followups_nov2_note_gap_unlinked.py tests/test_hint_feedback_texts.py -q -n 2 -m 'not arc_close'
# exit 0: 608 passed in 211.84s (0:03:31)

t.sh tests/test_hint_feedback_widening.py tests/test_mobile_v2_feedback.py tests/test_mobile_v2_followup.py tests/test_reader_followup_valuation.py tests/test_reader_followups.py tests/test_reader_followups_rereview.py tests/test_reader_followups_review.py tests/test_reader_followups_round3.py tests/test_reader_followups_round4.py tests/test_reader_followups_round5.py tests/test_reader_followups_round6.py tests/test_reader_followups_round7.py tests/test_reader_followups_round8.py tests/test_reader_followups_successor.py tests/test_source_retrieval_followup.py tests/test_t6_followup_composition.py tests/test_t6_followup_rereview.py tests/test_t6_followup_review.py tests/test_ux_phase4_feedback.py -q -n 2 -m 'not arc_close' -k 'not test_f1k_the_tui_open_defers_a_cold_check_a_routine_display_covers' -vv -o faulthandler_timeout=30
# exit 124: Runner stopped after 120 seconds; unverified.

t.sh tests/test_tui_feedback.py tests/test_ux_phase4_feedback.py::test_f1k_the_tui_open_defers_a_cold_check_a_routine_display_covers -q -n 2 -m 'not arc_close' -o faulthandler_timeout=30
# exit 124: Runner stopped after 120 seconds; unverified.

t.sh tests/test_tui_feedback.py::test_feedback_submit_uses_codex_grading_when_runtime_ready -q -n 2 -m 'not arc_close'
# exit 1: 1 failed in 2.02s

t.sh tests/test_identity_pins.py tests/test_retired_config_identities.py tests/test_diagnosis_journey_golden.py tests/test_structure_ratchets.py tests/test_mobile_allowlist.py -q -n 2 -m 'not arc_close'
# exit 0: 721 passed in 24.57s

t.sh tests/test_test_layout.py -q -n 1
# exit 0: 3 passed in 20.44s

t.sh tests/test_architecture.py -q -n 1
# exit 0: 18 passed in 31.85s

py.sh ruff check
# exit 0: All checks passed!

py.sh lint-imports --no-cache
# exit 0: Contracts: 43 kept, 0 broken.

t.sh tests/test_hint_feedback_widening.py tests/test_mobile_v2_followup.py tests/test_reader_followup_valuation.py tests/test_reader_followups.py tests/test_reader_followups_rereview.py tests/test_reader_followups_review.py tests/test_reader_followups_round3.py tests/test_reader_followups_round4.py tests/test_reader_followups_round5.py tests/test_reader_followups_round6.py tests/test_reader_followups_round7.py tests/test_reader_followups_round8.py tests/test_reader_followups_successor.py tests/test_source_retrieval_followup.py tests/test_t6_followup_composition.py tests/test_t6_followup_rereview.py tests/test_t6_followup_review.py tests/test_ux_phase4_feedback.py -q -n 2 -m 'not arc_close' -k 'not test_f1k_the_tui_open_defers_a_cold_check_a_routine_display_covers'
# exit 1: 297 passed, 4 errors in 17.46s

t.sh tests/test_tui_feedback.py tests/test_ux_phase4_feedback.py::test_f1k_the_tui_open_defers_a_cold_check_a_routine_display_covers -q -n 2 -m 'not arc_close' -k 'not test_committed_model_grade_is_not_regraded_when_a_later_step_fails' -o faulthandler_timeout=30
# exit 1: 1 failed, 5 passed in 4.53s

```

All 17 new tests are included in the passing first chunk. The named safeguards
include identity pins, retired configuration identities, the diagnosis journey
golden, structure ratchets and mobile allowlist: **721 passed**. No pin or golden
was moved or regenerated. Ruff passed; import contracts: **43 kept, 0 broken**.
The completed filename-selection runs verify **910 tests** (608 + 297 + 5);
blocked sockets, hung tests and partial interrupted-run output are excluded.

## Unverified checks and real-route limits

Five local fake-server tests cannot create a socket in this sandbox
(`PermissionError: [Errno 1] Operation not permitted`), and are **not verified**:

- `tests/test_t6_followup_composition.py::test_the_plan_route_gets_the_policy_budget_in_the_prompt_and_the_routes_effort`
- `tests/test_t6_followup_composition.py::test_a_plan_truncation_is_retried_once_on_the_subscription_with_no_output_cap`
- `tests/test_t6_followup_composition.py::test_the_latency_probe_asks_for_each_profiles_policy_budget`
- `tests/test_t6_followup_composition.py::test_a_truncated_latency_call_is_logged_and_failed`
- `tests/test_tui_feedback.py::test_feedback_submit_uses_codex_grading_when_runtime_ready`

The six tests in `tests/test_mobile_v2_feedback.py` are **not verified**. The
first one's `_answered` fixture stalls entering Starlette `TestClient`, in
AnyIO's thread-portal startup (`start_task_soon` / `run_sync_from_thread`);
its worker therefore never runs the other five. The diagnostic run was stopped
at 120 seconds. This is observed as a hang, not asserted to be a socket failure.

`tests/test_tui_feedback.py::test_committed_model_grade_is_not_regraded_when_a_later_step_fails`
is **not verified**: its stack remains in `asyncio.run()` shutdown
(`runners.close`, `run_until_complete`, selector wait) at 30 seconds; the
bounded run was stopped at 120 seconds. The other TUI cases and the TUI case
inside `test_ux_phase4_feedback.py` were rerun separately, producing the five
passes and one socket failure above. No unrelated test or application code was
changed to bypass these limitations.

No real model/provider call, external network call, private configuration/vault
read, live-route walk, manual UI rendering check, or real latency/token measurement was
performed. Fakes verify the request, receipt, workflow and serve behavior; the
supplied live measurement is not remeasured. Full-suite/arc-close and landing-gate
runs belong to the orchestrator. No `git add`, `git commit`, generated-reference
regeneration, CLAUDE.md edit or refactor-status.md edit occurred.

## Size and handoff

Production: **+56 / -6, net +50 lines (three files)**. All changes, including tests, ledger and this record: **+627 / -6, net +621 lines (six files)**.

All six changed files must be included, including the untracked test and this
record. Final `git diff --check`: exit 0, no output. Changes remain uncommitted
for the orchestrator on `fix/ux45-followup-empty-question`.
