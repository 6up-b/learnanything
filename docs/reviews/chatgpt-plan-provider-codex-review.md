# ChatGPT-plan provider: Codex review fixes

Stage: `providers/chatgpt-plan` (worktree `learnanything-chatgpt-plan`).
Reviewed code: `00f4a424` (the stage doc is `chatgpt-plan-provider.md`).
Review: Codex job `20261012-220738-d6PyD5`, 7 findings (1 High, 5 Medium,
1 Low), all reproduced and fixed. No finding was rejected.

## Review

### Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Sign-out can be undone by an in-flight refresh | fixed | `3e9c6a15` | `test_chatgpt_plan_signin.py`: `test_sign_out_during_an_in_flight_refresh_stays_signed_out`, `test_sign_out_invalidates_a_sign_in_that_was_already_pending`, `test_cancel_after_the_browser_returned_saves_nothing` |
| F2 | Medium | Credential acquisition bypasses cancellation and deadlines | fixed | `3e9c6a15`, `8f1c6f81` | `test_chatgpt_plan_provider.py`: `test_an_interrupt_while_waiting_for_the_refresh_lock_sends_nothing`, `test_a_deadline_that_passes_while_waiting_for_the_refresh_lock_sends_nothing`, `test_an_interrupt_during_the_token_refresh_keeps_the_new_tokens_and_sends_nothing`, `test_an_expired_deadline_is_never_extended_into_a_send`; `test_chatgpt_plan_signin.py::test_the_store_lock_gives_up_on_timeout_or_cancellation_but_not_when_free` |
| F3 | Medium | A concurrent success clears a newly imposed usage pause | fixed | `3e9c6a15` | `test_chatgpt_plan_provider.py`: `test_a_success_that_overlaps_a_usage_limit_keeps_the_pause` (guard: `test_a_success_clears_the_expired_pause_it_saw`) |
| F4 | Medium | Cancelling or reopening sign-in can leave Settings stuck | fixed | `9f67c1f3` | `ChatGPTPlanSettings.test.tsx`: "keeps polling after cancel until the attempt has actually ended", "resumes polling when Settings reopens during a sign-in" (guard: "does not announce an attempt that had already ended before Settings opened"); `test_chatgpt_plan_sidecar.py::test_cancel_and_failure_are_reported` (the cancel reply is final) |
| F5 | Medium | The latency command multiplies its metered spend cap | fixed | `20ea82f7`, `4cd73657` (help snapshot) | `test_chatgpt_plan_cli.py`: `test_latency_keeps_every_metered_provider_inside_one_dollar_cap`, `test_latency_stops_a_later_metered_provider_once_the_shared_cap_is_spent` |
| F6 | Medium | Refresh does not atomically replace tokens and granted permissions | fixed | `3e9c6a15` | `test_chatgpt_plan_signin.py`: `test_a_refresh_that_drops_plan_usage_never_serves_a_restricted_token[None, save_tokens, save_account, update_state]`, `test_a_reader_never_sees_new_tokens_with_the_old_grant` |
| F7 | Low | Credential renames are atomic but not crash-durable | fixed | `3e9c6a15` | `test_chatgpt_plan_signin.py::test_credential_files_are_durable_after_replace_and_delete` (marked `durability`, so it also runs in that lane) |

**Reproduction first.** Every test above was written before its fix and run
against the reviewed code (`src/` and the Settings component restored to
`00f4a424`): 17 failed, each for the reason the finding gives, e.g.

- F1: the account read `signed_in=True` after a sign-out that overlapped a
  refresh; a sign-in pending across a sign-out (or a cancel) saved its tokens.
- F2: an interrupt during lock contention still sent the prompt and returned
  `note='late'`; a deadline that passed during the wait still sent; a
  credential step that outlived the deadline still sent (`max(0.5, …)`).
- F3: `usage_exhausted → ready` after the overlapping success.
- F4: both vitest cases stayed on "waiting for the browser…" with no button.
- F5: the dry run exited 0 for $0.0928 against `--max-cost-usd 0.05`; with
  actual use above the estimate, the second provider still ran.
- F6: after a crash between the token and account writes (and also with no
  crash: the fast path ignored the grant) `access_token()` returned the
  restricted token; a concurrent reader got it during the commit.
- F7: the event log showed `fsync(file), replace(tokens.json)` and no
  directory fsync.

The guards (`[save_tokens]`, the expired-pause test, the vitest "does not
announce" case) pass on both versions by design: they pin behaviour the fix
must keep. The store-lock test (`8f1c6f81`) covers a gap found while fixing
F2: the first version of the cancellable lock refused a free lock when given
no time; it now always tries a non-blocking acquire first.

### What changed

**F1: one lock for every credential commit.** Sign-in, refresh and sign-out
all commit under `refresh.lock` and re-read the store inside it. Sign-out
takes the lock (so it waits for a refresh that already has its answer),
clears the tokens that are live at that moment, marks the account signed
out, and only then revokes the refresh token remotely, outside the lock (the
revoked token is the newest one, not the rotated-out one). It also advances a
`signout_epoch` in `state.json`. A `PendingSignIn` records the epoch when it
starts and is refused at commit if a sign-out happened since (`code =
"signed_out"`), or if it was cancelled (`code = "cancelled"`); either way its
fresh refresh token is revoked once, best effort, and nothing is saved. A
sign-in started after the sign-out works normally. `learnloop ai signout`
returns `ok: false` (exit 1) if the lock cannot be taken.

**F2: interrupts and deadlines reach the credential step.** The provider
publishes its `ResponsesStream` before the credential step, then calls
`access_token(timeout=<remaining>, cancelled=<interrupted or past deadline>)`.
The store lock polls `cancelled()` while waiting (`LockCancelled`) and is
bounded by the remaining time (`LockTimeout`); the refresh request's own
timeout is `min(20 s, remaining)`. After the token arrives the provider
rechecks both conditions and passes the exact remaining time to the stream;
`ResponsesStream.send` refuses a non-positive timeout instead of stretching it
to 0.5 s. A refresh whose answer has arrived is always committed, because its
refresh token has rotated (the test checks the session survives the
interrupt). The provider's `finally` clears `_active` only if it still holds
its own stream. The interrupt flag stays sticky, as for Codex clients (one
client per job). Other callers of `access_token()` now wait at most their
`timeout` (default 20 s) for another process's refresh, not 60 s.

**F3: compare and clear.** `check_usable()` returns the (expired) pause record
it saw; after a completed response the provider passes it to
`note_success()`, which removes `usage_limit` only if it is still that exact
record, compared under the state lock (`PlanStore.clear_state_if`). Each pause
record now carries a random `id`, so two pauses in the same second differ.

**F4: polling follows the attempt.** The Settings section polls while the
current attempt is `waiting`, keyed on the attempt id, so it starts after a
sign-in start, on mount when Settings reopens mid-sign-in, and keeps running
after cancel until the sidecar reports the attempt ended. Only an attempt this
screen saw waiting is announced (a toast on success, the error on failure); a
failing status call is reported once while polling continues. On the sidecar,
cancel now waits up to 2 s for the attempt to end, so its reply is usually
already `cancelled`; with F1, a callback already being finished is refused at
commit, so a cancelled attempt never saves.

**F5: one metered budget.** All metered providers draw on one `SpendBudget`
(`max_estimated_usd = --max-cost-usd`, calls and tokens summed). The combined
estimate is checked before anything runs: `--dry-run` reports `admissible`,
`reason` and `metered_estimated_usd` and exits 1 when over; a real run is
refused with `over_budget` before any client is built. Actual use above the
estimate is recorded and blocks the next metered call, so a later provider
stops with "stopped by the spend caps". Subscription profiles keep their own
estimate-only budget per provider; each row's `charged` is its own share.

**F6: one numbered generation for tokens and grant.** The token snapshot (in
the keyring or `tokens.json`) now carries its granted `scopes` and a
`generation`, and is written first; `account.json` then records the same
generation, the scopes, `plan_usage_enabled` and the access expiry (moved
there from `state.json`). Readers use a token only when the two generations
agree. Otherwise, under the lock, a newer snapshot is authoritative and the
interrupted commit is rolled forward; an older snapshot is refused ("sign in
again"). `access_token()` returns a token only under a grant that includes
`chatgpt.tokens.use.direct`, on every path (before, only right after a
refresh). Readiness and status still read `account.json` alone (never a
secret), so after a crash between the two writes they can say "ready" until
the next `access_token()` call, which rolls forward and refuses with "plan
usage not granted" before any request is sent. Snapshots written before this
change (no generation, no scopes) read as generation 0 and fall back to the
account's scopes.

**F7: directory fsync.** `_write_json` fsyncs the containing directory after
`os.replace`, and `FileSecrets.clear` after deleting `tokens.json`. A
filesystem that refuses `fsync` on a directory is tolerated (the file itself
is already synced).

**Also from the review's conformance table.** The fake server and the
request-shape test no longer import the implementation's
`UNSUPPORTED_FIELDS`: `tests/chatgpt_plan_fakes.py` keeps its own
`DOCUMENTED_UNSUPPORTED_FIELDS`, re-read on 2026-10-12 with a plain fetch (no
auth) from `developers.openai.com/siwc/token-sharing-open-source/preview-limitations`
(unchanged: the 15 fields, `previous_response_id` omitted over HTTP,
`role: system` items rejected, `store: false`, `stream: true`), plus
LearnLoop's tool-free rule. The test also asserts the implementation's list
covers the documented one. Two conformance notes are left for the owner (open
questions below): the ID-token TLS fallback and the logo.

### Spend and calls

No real paid or live call: no sign-in, no token store, `settings.env` or
`~/.config/learnloop` read, and no request to `auth.openai.com` or
`api.openai.com`. Every test uses the local fakes (a fake OAuth server and a
fake Responses SSE stream on 127.0.0.1) and a per-test `LEARNLOOP_CONFIG_DIR`.
One plain web fetch of a public docs page. `scripts/benchmark_chatgpt_plan_latency.py --calls 5`
(fakes only) still runs. Cost: $0.

### Gate

All on the final code (`4cd73657`; this file adds no code), `TMPDIR` in the
worktree's `fixtures-local/tmp`:

- `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`: done.
- `uv run lint-imports --no-cache`: **12 kept, 0 broken.**
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`:
  **8339 passed** (46 warnings), 4 min 54 s. An earlier run (before the
  lock follow-up `8f1c6f81`) had one failure,
  `tests/test_cli_help_snapshot.py`, because F5 changed the `ai latency` help
  text; the snapshot was regenerated
  (`uv run python tests/test_cli_help_snapshot.py --write`, `4cd73657`) and the
  rerun is the count above.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`:
  **88 passed, 8251 deselected** (the stage's 87 plus the new directory-fsync
  test).
- Frontend (`apps/learnloop-tauri`, unchanged since `9f67c1f3`): `npm install`;
  `npm run typecheck` clean (`tsc --noEmit` exit 0); `npm test` **26 files,
  124 tests passed** (the stage's 121 plus three); `npm run frontend:build`
  built.
- Schema unchanged (no migration, no new table), so the DB reference scripts
  were not needed. No Rust change; `cargo check` remains unrunnable on this
  machine (stage deviation 9).

### Open questions

1. **Sign-out invalidates every pending sign-in on the machine,** including one
   started in another process (a terminal sign-in begun before a desktop
   sign-out is refused at commit, and the user starts again). Is that the
   behaviour you want, or should only the desktop's own attempt be cancelled?
2. **ID-token signature fallback.** The reviewer notes the sign-in guide says
   to verify against the JWKS, while the stage falls back to the OpenID
   Connect TLS rule when the JWKS cannot be fetched (recorded per sign-in as
   `id_token_signature = "tls_endpoint"`, stage deviation 5). Keep the
   fallback, or fail the sign-in until the JWKS is reachable?
3. **Logo asset** (stage open question 5) is still open: the button has the
   approved label and black format but no ChatGPT logo.

## Re-review

Review: Codex job `20261012-225130-sURMIT`, on `49b73fc6`. Verdict: REOPENED,
with one new Low finding (F8). The reviewer confirmed F1 as fixed: sign-out
shares `refresh.lock` with credential commits, clears the latest tokens and
advances an epoch that rejects pending sign-ins. Its in-memory probes found
that a concurrent refresh cannot restore a sign-in and a stale sign-in cannot
commit. It raised nothing new on F2–F7.

### Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Sign-out can be undone by an in-flight refresh | fixed (confirmed by the re-review) | `3e9c6a15` | tests listed in the first table |
| F8 | Low | Aggregate budget rounding rejects a plan exactly at the cap | fixed | `91c82996` (fail-first test), `5cd0e284` (fix) | `test_chatgpt_plan_cli.py::test_latency_admits_a_metered_plan_exactly_at_the_shared_cap` |

**F8 reproduction.** The test asks for three metered profiles with
`--runs 1 --price-per-million 1000 --max-cost-usd 1.392`, which comes to
$0.464 per call. It failed on `49b73fc6` in the way the reviewer described:
the dry run exited 1 with `admissible: false`, because the float sum came to
`1.3920000000000001` and was over `$1.392`. The shared `SpendBudget` adds up in
decimal, so it would have admitted the same three calls.

**F8 fix.** `learnloop ai latency` now works out the per-call dollar figure
once, as `call_usd`, and every metered request reserves that same figure. The
plan totals in `Decimal`: each row is `Decimal(str(call_usd)) * runs`, and the
metered total is that times the number of metered providers. This matches how
`SpendBudget` adds up the per-call reservations, so the plan admits exactly
what execution admits. The regression test covers three cases:

- the dry run is admissible, with `metered_estimated_usd == 1.392`;
- the real run makes all three calls and charges `metered_charged_usd == 1.392`;
- a cap one tenth of a cent lower (`1.391`) is still refused with
  `over_budget` before any call.

The `ai latency` help text did not change, so the CLI help snapshot still
matches.

**Owner-directed item.** The faster subscription path for short structured
calls is the `chatgpt_plan` provider this stage builds: a direct Responses
call on the owner's ChatGPT plan, with no Codex process spawned. This fix step
needed no further work on it.

### Spend and calls

No real paid or live call was made. Nothing signed in, and nothing read a
token store, `settings.env` or `~/.config/learnloop`. No request went to
`auth.openai.com` or `api.openai.com`. The new test uses the existing fakes
(metered probe clients and a per-test `LEARNLOOP_CONFIG_DIR`). Cost: $0.

### Gate

All runs were on `5cd0e284` with `TMPDIR` in the worktree's
`fixtures-local/tmp`:

- `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`: done.
- `uv run lint-imports --no-cache`: **12 kept, 0 broken.**
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`:
  **8340 passed** (46 warnings), 4 min 35 s. That is the previous 8339 plus the
  F8 test.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`:
  **88 passed, 8252 deselected** (1 warning).
- The frontend did not change in this fix step, so the npm gate was not rerun.
  Its last result is in the first gate above: 124 tests passed.
- The schema did not change (no migration), so the DB reference scripts were
  not needed.

The open questions above (pending-sign-in scope at sign-out, the ID-token
signature fallback, the logo) are unchanged.
