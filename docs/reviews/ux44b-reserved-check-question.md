# UX-44b: reserve the certification check's question

## Measurement

The reported walk answered two of a topic's three questions correctly. At the
second answer a pending `certification_cold_probe` selected the third question,
with `not_before` fourteen days later. The ordinary list still offered that
unanswered question, allowing a full-list pick to spend its freshness.
Only these supplied field values are used; no personal vault was opened.

## Step 0 (recorded before code changes)

Read on base `1f9c8de1b3`. “Offers” means the reservation does not exclude the
item; other admission/ranking rules can still exclude it. These are pre-fix
answers for an open certification task whose selected question is not yet due.
Paths below are relative to `src/`.

| Surface | Before | Code / qualification |
|---|---|---|
| Due queue, including `read_due_queue` | offers | `learnloop/scheduling/scheduler.py`: `_due_queue`, `admission_reason`; `scheduling/serving_exclusions.py`: routine set reads only pending remediation items |
| Desktop Today's full list | offers | `learnloop_sidecar/handlers/queue.py`: `get_today_queue` calls `build_due_queue` |
| Today's book Begin and feedback Next | withholds | UX-44's `content/pipeline/add_source.py:reading_questions` reports `later_item_ids`; desktop `todayCause.ts` excludes them |
| Plan's eligible candidates and objective cold pool | offers | `daily_plan/engine.py:PlanEnv.build_eligible` uses the queue; `daily_plan/objective_inputs.py` reads routine exclusions |
| Plan's slot facts | withholds | `daily_plan/slot_facts.py` uses `out_of_timing_serving_exclusions` |
| Learner pick from full list | offers | `handlers/daily_plan.py:plan_learner_pick` and `daily_plan/engine.py:learner_pick`; no routine reservation refusal, and the list contains the item |
| Phone queue/list RPC | offers | same `get_today_queue`, with a device filter; device eligibility does not reserve certification questions |
| Phone Today book count / plan | withholds in book count; candidates offer | UX-44's shared `laterItemIds` fact already discounts it; plan uses shared engine |
| Terminal Today / selection | offers | `learnloop/tui/state.py:TuiState.refresh` builds the shared queue; `tui/screens/today.py` lists `state.queue` |
| MCP | withholds / no practice-serving selector | `learnloop_mcp/server.py:build_server` exposes learning-context and source tools, not a practice question selector |
| `find_practice` | withholds | `learnloop/practice_index` uses out-of-timing exclusions |
| Optional quick check | withholds | out-of-timing exclusions, also scheduler admission for Check once |
| Certification follow-up lane | withholds before due | `pending_followup_practice_items`, `_defer_revealed_cold_followups`, `_insert_pending_followups` in scheduler; due task insertion bypasses routine admission |

The check selects through `goals/certification_cold_probe.py:select_held_out_probe_item`:
unused certificate surface group, unshown material, active/renderable item,
preferring whole-task coverage and then least recently attempted. Scheduling
persists that selection and its horizon. On its day, untouched: the follow-up
lane inserts that question and the attempt consumer records its probe outcome.
Answered in between: `serve_eligibility._decide_cold_check` withdraws the task
with `cold_check_practised_since_scheduled` (or answer-shown disposition),
serves ordinary practice, and does not reselect another question. This is an
abstention from the measurement, not a new probe. The ordinary attempt must
be strictly later than task creation for the timestamp test to detect it.

Other cold kinds: `serve_eligibility.COLD_FOLLOWUP_TASK_KINDS` contains exactly
`cold_retry` and `certification_cold_probe`. A real pending remediation retry is
already withheld. A standalone `cold_retry` task without a matching live
remediation episode has the same routine gap (matrix `6.cold-task`, RT=S).
It is not widened here. `intervention_followup` and `negative_surprise_followup`
are not cold kinds. Pre-task remediation reservations intentionally remain
wider only outside routine serving.

## Rule and playbook decision

Add selected IDs of open (`pending` or `served`) certification tasks to the
routine `cold_check_reserved_item_ids`, retaining the pending-remediation set
and existing `cold_check_reserved` reason. Include that set in routine
`item_ids`. Keep the reservation while the task is open, including its due
window: its own follow-up insertion administers it, never the ordinary lane.
Do not add clock-dependent duplicate frontend rules. Terminal task states
release the reservation. An explicit pick is prevented by **not listing** the
question; this does not add a general raw-ID authorization boundary.

`docs/algorithm-change-playbook.md` requires a successor for persisted meaning,
including new measurement admission or priming even when replay is unchanged.
This changes ordinary serving availability only: no due date, evidence,
certificate, task selection/window, measurement eligibility, outcome label,
priming rule or replay derivation changes. A different future sequence of
learner choices is not a reinterpretation of recorded evidence. No tag is
needed. Precedent: `refactor-phase-1-fixes-protection.md` P5 introduced this
routine reservation and reason without an algorithm successor; `acd879b283`
then narrowed it to actual pending checks, also without a tag. K1-6's earlier
record overstates routine protection; P5 and its follow-up give the actual
implementation. Identity pins must remain unchanged.

The protection matrix has RT and OT surfaces, but no certification-task row.
Add the certification reservation's RT/OT cells using its existing world.

## What stays open

With only three questions, two answered and one reserved, no fresh question
may remain for fourteen days. Already-answered questions remain ordinary
review candidates and can still be picked from the full list (which includes
future reviews); the book's Begin
and Next do not offer them until due. With other questions still being written,
Today says it is writing and invites continued reading; otherwise it says
“Nothing from … is up today.” A done plan stays done unless extended. The
reserved question disappears from the list; `why`/slate exclusions carry
`cold_check_reserved`. This shortage already exists for cold retries; no
replacement generation, early release, horizon change, or new UI is added.
Stale displays, arbitrary raw-ID requests, other exposure paths, and UX-44c's
future-review wording are outside this list-reservation fix.

## Validation

The regression file uses the existing `_certify` vault from
`certification_cold_probe_helpers` (its explicit historical tag is unchanged),
a real certificate, and the production certification scheduler. The queue,
plan candidate builder, desktop full-list RPC, and phone-origin full-list RPC
all read the real task. The due-day test inserts it through the real follow-up
lane and consumes it through a self-graded attempt, checking the outcome's task
and attempt IDs. Expiry is tested from both `pending` and `served`. The matrix
adds isolated RT and OT cells on a copy of its existing clean held-grade item;
no unrelated cold-retry reservation confounds the OT cell.

Before production edits, the final regression selection gave **8 failed,
2 passed in 3.19s**. Failures were the queue, plan candidates, desktop full-list
pick availability, phone-origin list, the pre-day assertion of the due-day
journey, both open-state expiry journeys, and matrix RT. Every failure was at
an expected withholding assertion. Matrix OT already withheld and passed.
The no-reservation control passed on unchanged code: SHA-256 of complete,
canonical JSON queue rows (no fields dropped or normalized) was
`e25f79090b29aa2d0feeefe18eef007d09db6b4cf96e9ed085fa22bb9f395c30`.
It remains identical after the fix. This is the existing certified test vault
before scheduling any probe, not a newly invented expected row.

The first post-fix run reached and consumed the due check, then found a test
field-name mistake (`attempt_id` instead of `probe_attempt_id`). Corrected the
assertion; no production change. All eight tests in the new file subsequently
passed in the gates and core sweep. All 154 tests in the matrix passed in the
combined run. No identity pin, schema, migration, config, prompt or vault
reference was changed.

Commands below use `{SCRATCH}/t.sh` and `{SCRATCH}/py.sh` supplied in the brief;
all pytest invocations name explicit files, at most two workers. No socket-
blocked test is counted as passed. Inspection commands (`rg`, `sed`, `cat`,
`git log/show/diff/status`) were read-only; the initial broad ledger display
was truncated, then the exact UX-44b row was read with `rg`.

| Command / run | Result line |
|---|---|
| `t.sh tests/test_certification_serving_reservation.py tests/test_protection_surface_matrix.py -k 'reserved_question or reservation_cell or no_reservation' -q -n 2` (initial harness) | Interrupted, exit 130; phone TestClient stalled; no completed result counted |
| `t.sh tests/test_certification_serving_reservation.py -k 'not phone' -q -n 2` (initial harness) | `5 failed in 2.02s`: three real reservation failures, missing RPC registration in test setup, and placeholder baseline capture |
| Initial two-file selection again, after registering RPCs, pinning baseline, and using phone-origin RPC | `6 failed, 2 passed in 3.21s` |
| `t.sh tests/test_certification_serving_reservation.py tests/test_protection_surface_matrix.py -k 'reserved_question or reservation_cell or no_reservation or open_reservation' -q -n 2` (final fail-first) | `8 failed, 2 passed in 3.19s` |
| `t.sh tests/test_certification_serving_reservation.py tests/test_protection_surface_matrix.py -q -n 2` (first post-fix) | `1 failed, 161 passed in 35.47s`; test field typo above, matrix entirely passed |
| `t.sh tests/test_certification_serving_reservation.py tests/test_identity_pins.py tests/test_diagnosis_journey_golden.py tests/test_structure_ratchets.py tests/test_mobile_allowlist.py -q -n 2` | `709 passed in 30.55s`; no moved pin |
| Core sweep below | `379 passed, 9 skipped, 1 xfailed in 75.65s (0:01:15)` |
| Phone sweep below | Interrupted, exit 130 after two 60-second faulthandler dumps in TestClient startup; no completed suite result counted |
| `t.sh tests/test_test_layout.py -q -n 1` (alone) | `3 passed in 19.37s` |
| `t.sh tests/test_architecture.py -q -n 1` (alone) | `18 passed in 30.43s` |
| Socket-free phone subset below | `14 passed in 45.33s` |
| `py.sh ruff check` | `All checks passed!` |
| `py.sh lint-imports --no-cache` | `Contracts: 43 kept, 0 broken.` |
| `git diff --check` | Exit 0 |

The core sweep (33 explicit files):

```sh
{SCRATCH}/t.sh \
  tests/test_ad2_serving.py \
  tests/test_certification_cold_probe.py \
  tests/test_certification_serving_reservation.py \
  tests/test_characterization_certification_ledger.py \
  tests/test_daily_loop_lo_lifecycle_serving.py \
  tests/test_daily_plan_admission.py \
  tests/test_daily_plan_build.py \
  tests/test_daily_plan_composition.py \
  tests/test_daily_plan_kill_switch.py \
  tests/test_daily_plan_owner_decisions.py \
  tests/test_daily_plan_reading.py \
  tests/test_daily_plan_reentry.py \
  tests/test_daily_plan_replay.py \
  tests/test_daily_plan_review_regressions.py \
  tests/test_daily_plan_rpc.py \
  tests/test_daily_plan_split.py \
  tests/test_due_queue_golden.py \
  tests/test_due_queue_read_builds.py \
  tests/test_goal_certification_any_of.py \
  tests/test_instrument_serving.py \
  tests/test_k1_remediation_cold_reservation.py \
  tests/test_learner_pick_proposal.py \
  tests/test_remediation_cold_retry.py \
  tests/test_ro4_objective_serving.py \
  tests/test_ro6_serving.py \
  tests/test_router_r2a_serving.py \
  tests/test_router_r2b_serving.py \
  tests/test_scheduler.py \
  tests/test_scheduler_golden.py \
  tests/test_scheduler_probe_eig.py \
  tests/test_scheduler_requested_floor.py \
  tests/test_sidecar_remediation_surfaces.py \
  tests/test_sidecar_stops_serving.py \
  -q -n 2 -m 'not arc_close' -o faulthandler_timeout=60
```

The phone sweep (8 explicit files):

```sh
{SCRATCH}/t.sh \
  tests/test_mobile_v2_checks.py \
  tests/test_mobile_v2_feedback.py \
  tests/test_mobile_v2_followup.py \
  tests/test_mobile_v2_landing_fixes.py \
  tests/test_mobile_v2_objective_stop.py \
  tests/test_mobile_v2_plan.py \
  tests/test_mobile_v2_rereview_fixes.py \
  tests/test_mobile_v2_review_fixes.py \
  -q -n 2 -m 'not arc_close' -o faulthandler_timeout=60
```

The socket-free phone subset, after stopping the blocked sweep:

```sh
{SCRATCH}/t.sh \
  tests/test_mobile_v2_checks.py \
  tests/test_mobile_v2_followup.py \
  tests/test_mobile_v2_review_fixes.py::test_f5_the_open_randomized_check_is_named_cold_until_it_is_answered \
  tests/test_mobile_v2_rereview_fixes.py::test_f5_a_check_restored_from_its_checkpoint_the_next_day_stays_cold \
  tests/test_mobile_v2_plan.py::test_a_none_origin_never_enters_the_device_branch \
  -q -n 2 -m 'not arc_close'
```

The TestClient block is environmental: the worker stacks stop at
`starlette.testclient.__enter__` / `anyio.from_thread.start_task_soon`, before
LearnLoop's request handler. `py.sh python -c 'import socket; a,b=socket.socketpair(); a.close(); b.close()'`
exited 0, but the send/receive check
`py.sh python -c 'import socket; a,b=socket.socketpair(); a.settimeout(1); b.settimeout(1); a.send(b"x"); print(b.recv(1)); a.close(); b.close()'`
failed with `PermissionError: [Errno 1] Operation not permitted` (exit 1).
The event loop cannot wake through its local socket. The new phone test calls
the actual registered handler under `RequestOrigin`, without HTTP transport;
it failed before and passes after the reservation fix.

## Not verified

No live learner walk, browser, terminal UI interaction, HTTP phone journey,
external model or network call. No personal or optional local vault was read.
The nine core skips are absent optional fixtures, and the existing D-17 xfail is
not a pass. The socket-free phone subset above passed; the socket-blocked
phone tests and other tests not reached after the workers blocked remain unverified; they need the orchestrator's permitted
landing environment. The broader G6 matrix's previously undriven surfaces
remain outside this proof. No arbitrary-ID refusal or stale frontend list
invalidation change is claimed. No commit, staging, landing gate, or reference
regeneration was performed.

## Diff size and handoff

Five changed files; +380/-8 lines (net +372). Production is +15/-7 (net +8); the matrix
is +13, the new regression file +110, and the ledger status is +1/-1. The
remaining additions are this record. UX-44b is marked fixed in the working tree
of `fix/ux44b-reserved-check-question`, not yet committed or landed.

## Round 2: a check that is dead by date reserves nothing

The landing gate (the lane that runs over copies of real vaults; counts and
field values only) found one test failed, deterministically, with round 1 and
passes without it:
`tests/test_sidecar_contract.py::test_sidecar_get_knowledge_map_deterministic_and_geometric`.
It starts the sidecar twice on the same vault (initialize, then
`get_knowledge_map`) and requires equal results. With round 1 exactly one of
99 points differs in exactly one field, `queued`. The vault holds ONE
`followup_tasks` row of kind `certification_cold_probe` whose status is still
`pending` although its `expires_at` passed months ago (its `not_before` and
`expires_at` are a week apart, both long past). In the first run the task is
still pending when the map is computed, so round 1 withholds its selected
question (`queued` false); during that same run the sidecar's housekeeping
marks the task `expired` (the vault's `followup_tasks` row changes and a
`goal_lifecycle_events` row is written); in the second run the question is
queued again. Without round 1 the map does not depend on the task and both
runs agree. Round 1 reserves the question of a task that is OPEN BY STATUS
BUT DEAD BY DATE. A reservation must hold only while the check can still be
administered. These are the supplied observations; no real vault was opened.

The reused predicate is `serve_eligibility.FollowupTask.unexpired(at)`, via
`FollowupTask.from_row(task)`. The follow-up lane's `_decide_cold_check` uses
this predicate before its `due(at)` check. The latter additionally requires
`not_before <= at`; requiring that for reservation would spend the question
before its day, so reservation uses **unexpired**, including the future
window. `open_followup_tasks_of_kind` supplies the `pending`/`served` status
filter. Expiry is inclusive: exactly at `expires_at` still reserves; after
it reserves nothing. No second date predicate was introduced.

The store's `pending_followup_practice_items(clock=...)` calls
`due_followup_tasks(clock=...)`. On a writable attach the latter lazily
marks open tasks expired when `expires_at < utc_now_iso(clock)` and releases
cold-retry episodes with no open replacement. On a read-only attach it
performs the same dated selection without the marks. `_due_queue` reads
routine exclusions before that follow-up read: this ordering explains the
first-read discrepancy. The fix makes reservation independent of the lazy
mark; it does not move or add housekeeping writes.

At initialize, `SidecarContext.load` calls
`schedule_certification_cold_probes` without a supplied clock (its existing
`SystemClock` boundary). Certification scheduling cancels withdrawn or
superseded certificates through `expire_followup_task`; an unchanged
certificate's existing task is retained regardless of date. It is the lazy
follow-up read that expires its elapsed window. Initialize also calls the
separate `router_objective.goal_lifecycle.sweep`, whose events describe goal
YAML changes, using its supplied clock or the existing system-clock default.
The store's date-expiry update itself does not write a goal lifecycle event.

Every routine-exclusion caller now passes an explicit instant:

| Caller | Time passed |
|---|---|
| `scheduler._due_queue` | Its existing UTC `now`, resolved from the build/read caller's clock (or the scheduler entry's existing `SystemClock` default) |
| `scheduler._outside_build_admission` | Its required `now` from the admission caller, also used to build its `FrozenClock` |
| `daily_plan.objective_inputs.check_eligible_items` | New required keyword `now`; both engine callers, `_draw_randomized_checks` and `_checks_to_place`, supply `env.now()` |
| `out_of_timing_serving_exclusions` | One `now = clock.now()` shared by its task filter, reveal window and routine exclusions; `clock` is now required |

No exclusion function reads the wall clock or silently supplies a default.
The out-of-timing callers also resolve time explicitly: plan `slot_facts`
passes `FrozenClock(env.now())`; scheduler placement, `PracticeAdmission.load`
and quick-check candidate selection pass their supplied clock, or explicitly
construct `SystemClock()` at that caller boundary when the existing optional
clock is absent. `PlanEnv.now()` already resolves its optional clock there.
The objective reader previously had no clock argument and now requires one
instant at its own entry point. Test callers pass their fixture's clock or
instant; their existing assertions and protection matrix cells are unchanged.

Point 3: the out-of-timing **task loop** had exactly the same status-only gap.
It now uses the same one-line `FollowupTask.unexpired` filter, for all supplied
cold task kinds. A standalone expired cold-retry task therefore stops reserving
through that loop too. The **episode reservation** remains a separate gap:
`pending_remediation_cold_item_ids` and `open_remediation_cold_item_ids` both
use `_remediation_cold_item_ids`, an SQL `EXISTS` over pending/served retry
rows without a date. They can reserve an episode's cold item until lazy
expiry marks its last retry and `_release_cold_reservation` abandons its
`cold_scheduled` episode. The wider method also intentionally holds pre-task
episodes awaiting their primed attempt. Fixing these needs a dated episode
query/API, not a one-line use of the shared task predicate, so it is listed
and left unchanged under point 3. It can still contribute that item through
the routine or out-of-timing episode union despite the corrected task loop.

Fail-first regressions extend `test_certification_serving_reservation.py`:
complete queue rows, plan candidate rows, and full-list handler sections equal
the same vault's no-task baseline when a pending task has a past window.
Each also asserts the selected item is available (pickability means the
full-list availability boundary of round 1, not a new arbitrary-ID gate).
Queue and direct knowledge-map handler reads agree before/after the actual
lazy expiry, with the pending-to-expired transition asserted. These use the
existing certified vault helper and no sockets or startup worker. Opposed
wall/caller dates exercise the queue, outside-build admission, and
out-of-timing selectors in both directions. The wall date is simulated for
repeatability; the historical pinned-live case also predates the actual date
of this review. The live controls and all eight round 1 tests still pass.

The initial harness mistakenly supplied `clock` to `exclusion_now`, which
has no such argument: `9 failed, 2 passed in 2.80s` included two TypeErrors.
After using the actual clock-bearing `pool_admission(now=...)` entry, the
final fail-first run on unchanged round 1 production code was **8 failed,
3 passed in 2.76s**. All failures were behavioral assertions: the three
baseline surfaces, queue and map equality across housekeeping, and the three
expired-at-caller-time cases. The three pinned-live controls already passed.

Round 1's `cold_check_reserved` reason, serving surfaces, certification matrix
cell and no-tag decision remain. No schema, algorithm identity, certificate
selection, due window, outcome meaning or replay derivation changes. UX-44b's
ledger retains `fixed on fix/ux44b-reserved-check-question, not yet landed`
(with the branch formatted as code in the ledger). Its regression wording now
states that a task dead by date reserves nothing at the caller's clock.

Validation commands use the supplied `{SCRATCH}/t.sh` and `{SCRATCH}/py.sh`
wrappers, abbreviated below as `t.sh` and `py.sh`. Inspection used read-only
`cat`, `sed`, `rg`, and `git status/diff`; no staging or commit command ran.
The core sweep is the 33 explicit files in round 1's core command above plus
`tests/test_knowledge_map_text_neighbors.py` (34 files, one chunk). It used
`-q -n 2 -m 'not arc_close' -o faulthandler_timeout=60 --tb=short`.

| Command / run | Result line |
|---|---|
| `t.sh tests/test_certification_serving_reservation.py -k 'dead_by_date or pinned_date' -q -n 2` (initial harness) | `9 failed, 2 passed in 2.80s`; two harness TypeErrors as above |
| Same command plus `--tb=short` (corrected fail-first) | `8 failed, 3 passed in 2.76s` |
| `t.sh tests/test_certification_serving_reservation.py tests/test_protection_surface_matrix.py -q -n 2 --tb=short` | `173 passed in 36.56s` |
| `t.sh tests/test_identity_pins.py tests/test_diagnosis_journey_golden.py tests/test_structure_ratchets.py tests/test_mobile_allowlist.py -q -n 2 --tb=short` | `701 passed in 20.48s`; no moved pin or golden |
| Core sweep (34 files, specified above) | `407 passed, 9 skipped, 1 xfailed in 68.59s (0:01:08)` |
| `t.sh tests/test_ad23_inversion.py tests/test_attempt_content_state_successor.py tests/test_exam_protection_review.py tests/test_followup_single_use.py tests/test_ro5_checks.py tests/test_teacher_te2_probes.py -q -n 2 -m 'not arc_close' -o faulthandler_timeout=60 --tb=short` | `160 passed in 23.98s` |
| `t.sh tests/test_test_layout.py -q -n 1 --tb=short` (alone) | `3 passed in 19.56s` |
| `t.sh tests/test_architecture.py -q -n 1 --tb=short` (alone) | `18 passed in 30.59s` |
| `py.sh ruff check` (initial and final) | `All checks passed!` |
| `py.sh lint-imports --no-cache` (initial and final) | `Contracts: 43 kept, 0 broken.` |
| `git diff --check` | Exit 0 |

The nine core skips are absent optional fixture copies; the existing D-17
xfail is not a pass. No socket-blocked test is counted as passing.

Not verified: the copied-real-vault landing lane, the original sidecar
subprocess gate on those vaults, live UI/phone transport, or real model calls.
The new socket-free handler regression reproduces the queue/map discrepancy;
it does not claim to have rerun that external gate. No personal vault,
optional local fixture, global configuration, environment file, or credential
was opened. No network/model calls, reference regeneration, staging, commit,
landing, or edits to `refactor-status.md` or `CLAUDE.md` were performed.

Round 2 diff from the committed round 1 plus references: 18 files, +283/-44 (net +239).
Production: +28/-24 (net +4); tests: +108/-19 (net +89).
All changes are unstaged; the branch remains fixed here, not yet landed.
