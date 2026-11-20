# UX-39: a live background plan stream survives the old total deadline

Branch `fix/ux39-live-stream-deadline`, base `1119b97462`. Uncommitted implementation record.

## Measurements (supplied live-route verification)

First web chapter: about 28,000 source characters; about 9,500–12,100 output tokens.
Four synthesis completions took 193, 206, 245 and 260 seconds. Another was still
running at 410 seconds. Another was cut at exactly 480 seconds, then its automatic
identical retry was cut at exactly 480 seconds. Output was arriving at the cuts.
Six-topic question writing also hit 480 seconds (that caller is now split per topic).
Observed speed varies by a factor of two or more.

## Step 0 (written before production changes)

- `content/pipeline/jobs.py:INGEST_CODEX_TIMEOUT_SECONDS = 8 * 60` supplies 480 to
  inventory and synthesis clients, including the synthesis client used for authoring.
  `ai/routing.py:client_for_provider` passes the caller timeout for turn transports;
  `ai/client.py` copies it over the profile timeout. `complete()` chooses request,
  profile, then transport default, in that order. Execution scopes supply budgets,
  observations and single-request policy, but no progress deadline.
- `ResponsesStream.send` starts a fixed timer; `_stop_if_due` also checks only total
  elapsed time. `_read_stream` parses individual SSE events and has `on_event`;
  text deltas are accumulated locally. Thus output progress is observable without
  changing anything sent to the model. Cancellation shuts down the socket to wake reads.
- A cut raises `StreamCancelled`, mapped to `AITurnTimeout`. The physical and wrapper
  receipts finish failed, with the exception type. Partial deltas are lost; no terminal
  usage exists, so token counts are unknown, not zero measured tokens. No partial JSON
  is validated or checkpointed. `ModelCheckpoint` keeps only successful complete answers;
  inventory windows and synthesis passes/shards already kept are reused on retry.
- `retries_on_its_own` gives automatic inventory/bootstrap/append jobs (and section
  practice expansion) two tries in the same claim. `a_retry_may_cure` includes timeouts.
  The second try asks again for the missing answer under the same 480-second bound.
  When this answer needs longer at the route's current speed, neither try can finish.
- Foreground grading, tutor/Ask, hint writing, lessons and reader follow-ups use the
  profile timeout, else `ai.timeout_seconds` (180 seconds by default); explicit request
  timeouts still win. Other foreground bounds include hint chooser 3 seconds,
  reader intent and comparison scope 4 seconds, router LLM 40 seconds (prefetch 45),
  and daily-plan teach-back 120 seconds. Tutor retrieval has a separate 15-second
  retrieval bound. Direct CLI goal-practice authoring keeps its 900-second total;
  the separate diagnosis host keeps its 300-second total. None may inherit ingest
  behavior from a purpose string.
- Ingest's 120-second lease is renewed every 15 seconds alongside blocking calls;
  it detects dead workers and is **not** a job runtime limit. There is no applicable
  per-ingest-job absolute time limit. Unrelated diagnosis and inquiry leases are not
  ingest limits. The plan transport has no concurrency semaphore. The host's write
  guard and receipt scopes do not hold a database transaction across the stream;
  inventory worker contexts are copied. The worker lane stays occupied, but the new
  policy will remain bounded, never open-ended.

## Chosen rule and judgment calls

The ingest host explicitly scopes background work; the structured request carries a
boolean field, default false. Only the plan transport interprets it. Foreground keeps
the existing total deadline exactly. No purpose-string inference.

Background uses the configured provider timeout **before** the 480-second job override
as its idle window, falling back to `ai.timeout_seconds` (180 seconds by default).
Direct profile construction falls back to the transport's existing 180-second default.
There is no distinct plan connect/read setting. A nonempty output delta (including
reasoning) refreshes activity; SSE keepalives and lifecycle events do not.

The absolute ceiling is a named module constant, 1,200 seconds (20 minutes), because
the renewable job lease cannot supply one. This is 2.5 times the failed 480-second
bound and over twice the observed unfinished 410-second call, allowing the measured
twofold speed variation without letting endless output occupy the worker forever.
This is an operational bound, not a prediction of live completion time. No config field,
schema, migration, algorithm tag, prompt, routing, budget or checkpoint key changes.

Ceiling timeouts retain `AITurnTimeout` and carry a reason that the host refuses to
retry automatically; idle timeouts remain eligible for the existing one retry.
Both ultimately use the existing failed build state and Try again action. A manual
Try again remains available; completed checkpoints are still reused.

## Implementation and invariants

`_batch_unit` scopes `background_model_work`; `execute_structured_operation` copies
that ownership into `StructuredRequest.background`. The inventory pool already uses
`copy_context().run`; a test checks inheritance and restoration. No other host opts in.
The client factory preserves the profile timeout before the job override as a client
attribute, outside config dumps and model settings. A small deadline value carries
the total bound and optional idle window through the provider's existing paths.

The stream watchdog wakes at the earlier bound, rescheduling only when output moved
the idle bound. It does not start a thread for every token. Empty deltas, comments,
lifecycle events and malformed events do not refresh it. Reasoning deltas do. Token
acquisition is also idle-bounded; cancellation there sends no request. A cut still
discards partial JSON and leaves unknown usage; the physical receipt additionally
names `idle`, `ceiling`, `deadline` or `interrupt` as its finish reason.

`AITurnTimeout.reason` distinguishes cuts without replacing the exception class.
The runner persists `timeout_ceiling` for a ceiling, so `retried_on_its_own` cannot
claim a retry that did not happen; idle retains the existing `timeout` code. This is
an error value in existing JSON, not a schema change. The full first-document journey
checks the failed state, missing pass checkpoint, call count and existing Retry action.

One cancellation detail needed fixing: `http.client.getresponse()` can detach a
`Connection: close` socket from the connection while the response still owns its reader.
Keep the socket reference before that happens and close the response in `finally`.
Otherwise the watchdog can set its reason without waking the blocked reader. The real
local-server test covers the wakeup; the deterministic detached-socket test checks
shutdown at the exact idle deadline. Both stop and quit still call the existing interrupt.

Tool-free request construction, schemas, budgets, model settings and routing are
unchanged. A successful foreground/background pair sends equal request bodies, with
no `background` wire field. `single_request()` still sends one physical request;
the module's existing transient/refresh/repair policy outside it is unchanged.

## Fail-first evidence

The first behavioral run used unchanged production sources at `1119b97462`, before
implementation: **8 failed, 1 passed**. An earlier setup run failed all nine because
the fake URL was not loopback; correcting that test setup produced the meaningful run.

| Test | Before | After |
|---|---|---|
| Live background stream through 710 seconds | `AITurnTimeout` at 480 | completes, one body |
| Same foreground stream | passes: shutdown at 480 | same (preservation guard, not a claimed failing test) |
| Output at 100, then silence through 300 | no timeout | idle shutdown at 280 |
| Lifecycle-only or empty delta | no timeout (two cases) | idle shutdown at 180 |
| Reasoning output through 710 | cut at 480 | completes |
| Endless stream in automatic synthesis job | two requests | one, ceiling at 1,200; failed, not marked retried |
| Idle cut in automatic inventory job | completes once | two attempts, failed |
| Interrupt at 600 during background output | timeout at 480 before interrupt | `AIInterrupted` at 600 |

Supplementary fail-first checks:

- Full synthesis journey with the original runner temporarily restored: **1 failed,
  1 passed**. Ceiling made two calls instead of one; idle was already curable. The
  working runner was restored immediately. Both cases pass with the fix.
- Detached-socket shutdown against the first implementation: **1 failed** (`None`
  instead of shutdown time 280); passes after retaining the socket reference.
- A socket timeout racing the watchdog at the ceiling was initially labeled idle:
  **1 failed** before the correction. The socket exception path now compares the
  absolute bound too, so it cannot authorize an identical automatic retry.
- Other guards cover stop/quit at 600, context inheritance/reset, original-profile
  idle selection, identical wire bodies, token acquisition and timer cleanup.

## Sandbox limits and verification judgments

- Local TCP socket creation is denied with `PermissionError: [Errno 1] Operation not
  permitted`. Neither new socket test ran its assertions. Existing plan-server tests
  have the same restriction; none is counted as passing. They remain ordinary tests
  for the orchestrator's unrestricted landing gate, without skips or weakened assertions.
- `test_mobile_v2_plan.py` and `test_mobile_v4_plan.py` hang entering Starlette's
  `TestClient` in their fixture, before model code. The 60-second stack dump locates
  that wait; each was stopped by the 120-second command guard. A bare
  `TestClient(Starlette())`, importing no LearnLoop module, also hangs (10-second guard).
  These files are unverified, not attributed to the deadline change or counted as passes.
- Running `test_plan_determinism_landing.py` alone reveals its pre-existing reliance
  on another collected file importing `learnloop_sidecar.handlers`: 15 `KeyError:
  get_daily_plan` failures. Its helper reads an unpopulated registry. The follow-up
  pairs it with `test_plan_determinism.py`, which imports the handlers, as the original
  requested chunk does. No unrelated test or production registry code is changed.
- An initial overlapping pair of pytest commands triggered stale-temp cleanup across
  the sandbox's process namespaces (561 setup errors). That run is discarded. The
  replacement broad chunk stalled in the mobile fixture and was interrupted; the final
  runs below use individual explicit files, sequentially, with at most two workers.
- No live route, model call, network request, personal vault, configuration secret,
  desktop walkthrough or landing gate was verified. The 20-minute ceiling is a
  bounded operational judgment based on the supplied timings, not a live benchmark.

## Commands and results

`T` below means the supplied `{SCRATCH}/t.sh`; `P` means `{SCRATCH}/py.sh`. Paths
in commands are repository-relative. Results count actual passes only, never blocked
socket tests. No whole suite, `git add`, `git commit`, golden regeneration or vault
reference regeneration was run.

Each row below is one exact invocation of:

```sh
timeout --signal=INT --kill-after=5 120 T FILE -q -n 2 -m 'not arc_close' -o faulthandler_timeout=60
```

The file set was the sorted `tests/test_*.py` names containing `chatgpt_plan`,
`plan`, `transport`, `responses`, `timeout`, `interrupt`, `ingest_runner`,
`first_questions` or `synthesis` (55 files including the new tests). A file is
one-file chunk, below the 40-file maximum. `test_sim_planted_types_forty_seeds`
contains only excluded arc-close cases (exit 5), not a passing test.

| FILE | Result line |
|---|---|
| `tests/test_chat_total_transport_deadline.py` | 13 passed in 6.30s |
| `tests/test_chatgpt_plan_cli.py` | 1 passed, 10 errors in 2.41s |
| `tests/test_chatgpt_plan_deadline.py` | 16 passed in 1.99s |
| `tests/test_chatgpt_plan_deadline_socket.py` | 2 failed in 1.18s |
| `tests/test_chatgpt_plan_landing.py` | 1 error in 1.98s |
| `tests/test_chatgpt_plan_provider.py` | 1 failed, 1 passed, 26 errors in 2.33s |
| `tests/test_chatgpt_plan_sidecar.py` | 1 passed, 4 errors in 2.79s |
| `tests/test_chatgpt_plan_signin.py` | 25 failed, 4 passed in 1.69s |
| `tests/test_chatgpt_plan_workspace.py` | 5 passed, 22 errors in 2.31s |
| `tests/test_codex_transport_retired.py` | 6 passed in 2.02s |
| `tests/test_curriculum_c1_plan_follows_path.py` | 25 passed in 9.17s |
| `tests/test_daily_plan_admission.py` | 7 passed in 1.08s |
| `tests/test_daily_plan_build.py` | 19 passed in 2.74s |
| `tests/test_daily_plan_composition.py` | 3 passed in 9.50s |
| `tests/test_daily_plan_kill_switch.py` | 6 passed, 3 skipped, 1 xfailed in 3.04s |
| `tests/test_daily_plan_owner_decisions.py` | 7 passed in 3.10s |
| `tests/test_daily_plan_reading.py` | 7 passed in 27.45s |
| `tests/test_daily_plan_reentry.py` | 5 passed in 2.86s |
| `tests/test_daily_plan_replay.py` | 2 passed in 4.98s |
| `tests/test_daily_plan_review_regressions.py` | 29 passed in 4.73s |
| `tests/test_daily_plan_rpc.py` | 10 passed in 16.74s |
| `tests/test_daily_plan_split.py` | 10 passed in 0.99s |
| `tests/test_first_questions_arrive.py` | 1 failed, 16 passed in 11.34s |
| `tests/test_first_questions_today.py` | 22 passed in 16.56s |
| `tests/test_followups_batch6_prefetch_plan_wait.py` | 7 passed in 3.91s |
| `tests/test_ingest_runner.py` | 65 passed in 4.11s |
| `tests/test_intent_plan.py` | 12 passed in 2.66s |
| `tests/test_intent_planner.py` | 3 passed in 1.87s |
| `tests/test_mobile_v2_plan.py` | 120-second guard: exit 137; fixture did not return, unverified |
| `tests/test_mobile_v4_plan.py` | 120-second guard: exit 137; fixture did not return, unverified |
| `tests/test_plan_determinism.py` | 14 passed in 16.87s |
| `tests/test_plan_determinism_landing.py` | 15 failed, 1 passed in 3.18s |
| `tests/test_plan_first_transport.py` | 24 failed, 32 passed in 8.16s |
| `tests/test_plan_first_transport_grant_scope.py` | 10 passed in 2.62s |
| `tests/test_plan_first_transport_offer_grants.py` | 19 passed in 28.04s |
| `tests/test_plan_first_transport_offer_grants_r5.py` | 9 passed in 7.83s |
| `tests/test_plan_first_transport_paid_roles.py` | 3 failed in 2.02s |
| `tests/test_plan_first_transport_today_quiet.py` | 2 passed in 2.66s |
| `tests/test_plan_follows_path.py` | 17 passed, 3 skipped in 3.91s |
| `tests/test_plan_refs.py` | 5 passed in 1.04s |
| `tests/test_planted_misgrade.py` | 8 passed in 9.08s |
| `tests/test_sidecar_synthesis.py` | 1 passed in 2.72s |
| `tests/test_sidecar_transport.py` | 5 passed in 1.74s |
| `tests/test_sim_planted_types_forty_seeds.py` | no tests ran in 1.11s |
| `tests/test_source_set_synthesis.py` | 43 passed in 4.29s |
| `tests/test_structured_transport_parity.py` | 26 passed in 2.08s |
| `tests/test_synthesis_answer_reuse.py` | 6 passed in 2.24s |
| `tests/test_synthesis_criterion_dependencies.py` | 9 passed in 3.30s |
| `tests/test_synthesis_eval.py` | 5 passed in 2.18s |
| `tests/test_synthesis_gates.py` | 4 passed in 1.00s |
| `tests/test_synthesis_identifiability.py` | 6 passed in 1.88s |
| `tests/test_synthesis_manifests.py` | 3 passed in 1.88s |
| `tests/test_synthesis_runs_repo.py` | 5 passed in 1.81s |
| `tests/test_synthesis_sweep_primary_only.py` | 4 passed in 4.89s |
| `tests/test_synthesis_tail_golden.py` | 25 passed in 4.02s |

All 119 socket-related failures/errors in the table are the denied local socket
creation, not passing tests. The 15 registry-order failures disappear in the paired
run below. Counting each selected test once after that paired run: **577 passed (including the final additional timeout-race guard),
6 skipped, 1 xfailed**, plus the 119 socket-blocked cases, the two unverified mobile
files and the excluded arc-close file. No assertion was relaxed to get these results.

Other verification commands (the `T`/`P` notation is defined above):

| Command | Result line / interpretation |
|---|---|
| `T tests/test_chatgpt_plan_deadline.py -q -n 2` (initial setup) | 9 failed in 1.71s: fake non-loopback URL rejected; corrected before the behavioral run |
| `T tests/test_chatgpt_plan_deadline.py -q -n 2` (unchanged source) | 8 failed, 1 passed in 1.72s: fail-first table above |
| `T tests/test_chatgpt_plan_deadline.py tests/test_identity_pins.py -q -n 2` (first implementation) | 354 passed in 15.67s |
| `T FILES -q -n 2 -m 'not arc_close'` (initial 54-file selection, first 40) | 6 skipped, 1 xfailed, 561 errors in 10.40s; invalid concurrent-temp run, discarded |
| Same command, remaining 14 | 142 passed in 12.17s; rerun per file above |
| `T tests/test_retired_config_identities.py tests/test_structure_ratchets.py tests/test_effective_defaults_golden.py tests/test_kill_switches.py tests/test_sqlite_file_copies.py tests/test_mobile_allowlist.py -q -n 2` (first implementation) | 367 passed in 10.30s |
| `T tests/test_chatgpt_plan_deadline.py tests/test_chatgpt_plan_deadline_socket.py -q -n 2` | 2 failed, 13 passed in 1.96s; both failures are socket denial |
| `T FILES -q -n 2 -m 'not arc_close'` (55-file selection, first 40) | interrupted, exit 130, stalled in the mobile fixture; no completed result counted; second chunk did not start |
| `T tests/test_chatgpt_plan_deadline.py::test_idle_watchdog_can_shutdown_a_socket_detached_by_http_close -q -n 2` | 1 failed in 1.04s before the socket-retention fix |
| `T tests/test_chatgpt_plan_deadline.py tests/test_first_questions_arrive.py tests/test_identity_pins.py -q -n 2` (final source) | 1 failed, 377 passed in 25.31s; failure is the existing first-questions local-server test, blocked by socket denial; all 345 identity pins pass |
| `T tests/test_first_questions_arrive.py::test_synthesis_timeout_reason_controls_retry_and_keeps_try_again -q -n 2` (original runner restored temporarily) | 1 failed, 1 passed in 3.01s; ceiling sent two calls; restored working runner after run |
| `T tests/test_plan_determinism.py tests/test_plan_determinism_landing.py -q -n 2 -m 'not arc_close'` | 30 passed in 30.98s; the registry is populated by the companion file's existing import |
| `T tests/test_retired_config_identities.py tests/test_structure_ratchets.py tests/test_effective_defaults_golden.py tests/test_kill_switches.py tests/test_sqlite_file_copies.py tests/test_mobile_allowlist.py -q -n 2` (final source) | 367 passed in 10.14s |
| `T tests/test_test_layout.py -q -n 1` (alone) | 3 passed in 19.86s |
| `T tests/test_architecture.py -q -n 1` (alone) | 18 passed in 30.96s |
| `T tests/test_chatgpt_plan_deadline.py::test_socket_timeout_at_ceiling_is_not_mistaken_for_retryable_idle -q -n 2` | 1 failed in 1.09s before the classification correction |
| `T tests/test_chatgpt_plan_deadline.py tests/test_first_questions_arrive.py tests/test_identity_pins.py -q -n 2` (after timeout-race correction) | 1 failed, 378 passed in 26.47s; same existing socket-blocked test; all 17 deadline tests and 345 identity pins pass |
| `P ruff check` (initial, intermediate and final source) | All checks passed! |
| `P lint-imports --no-cache` (intermediate and final source) | Contracts: 43 kept, 0 broken. |
| `git diff --check` | clean |

For the initial 54-file selection, `FILES` is the table's sorted file list excluding
`test_chatgpt_plan_deadline_socket.py`, split at 40. The interrupted replacement uses
the table's 55-file list, also split at 40. Only the later per-file results are counted.

Fixture diagnostic commands:

```sh
timeout --signal=INT --kill-after=2 10 P python -c 'from fastapi import FastAPI; from starlette.testclient import TestClient; print("entering bare TestClient", flush=True); client = TestClient(FastAPI()); client.__enter__(); print("entered", flush=True); client.__exit__(None, None, None)'
```

Result: exit 1, `ModuleNotFoundError: No module named 'fastapi'` (the app uses Starlette).
Corrected minimal reproduction, without importing LearnLoop:

```sh
timeout --signal=INT --kill-after=2 10 P python -c 'from starlette.applications import Starlette; from starlette.testclient import TestClient; print("entering bare TestClient", flush=True); client = TestClient(Starlette()); client.__enter__(); print("entered", flush=True); client.__exit__(None, None, None)'
```

Result: prints `entering bare TestClient`, hangs, then exit 137 under the guard.

## Size and remaining verification

Production: **+165/−30, net +135 lines** across seven files (below 300 added production lines). Total diff including tests and this record: **+901/−30, net +871 lines** across thirteen files. No existing test assertion was changed.

The orchestrator must run the blocked socket assertions and mobile files outside
this sandbox, commit the diff, and run the landing gate. No live-route success is
claimed. The unchanged identity/config goldens were checked, not regenerated.
