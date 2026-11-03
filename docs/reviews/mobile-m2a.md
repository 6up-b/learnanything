# Mobile M2a: typed practice on the phone

Stage `mobile-m2a`, branch `mobile/m2a` in `learnanything-merge2`, base `6cf7a91ba8` (migration head 238, latest algorithm
`mvp-0.43`). Spec: `docs/specs/spec_mobile_tailnet_v1.md` §9 (M2a row), §3.1, §3.4, §4.5, §6.1, §6.2, §6.3, §6.4, §6.5, §6.8, G1-G12; as-built note §9.9.

**The owner decided on 2026-11-03 to build now:** M1's roughly two weeks of captures are waived, and the owner runs phone
checks A1-A4 later (§7 below lists them, with commands). M1's own gate ("captures per week") therefore has no data behind it,
by the owner's choice. No automated check here touches Tailscale or a real phone, so **A1-A4 are unverified**.

No model calls and no paid calls; synthetic vaults only; fake identity header and fake grader throughout.

## Commits

| Group | What |
|---|---|
| Host and adapter | `/rpc`, the M2 allowlist, `adapter.py`, `runtime.py` (two workers in secondary attach), `GET /api/v1/queue-revision`, `/app/` serving, the start bump, the phone's offer logging, the M2 report |
| Jobs | Migration 240, head fixture 240 and the mechanical test renames, `capture/jobs.py` wired in, restart recovery, job and submission status, G7, G6b |
| Handoff | The desktop's adopt, start fresh and cancel prompt, the banner reading `useSessionMoved`, the frozen question, `adopt_session` in Tauri, G10 |
| PWA | `apps/learnloop-mobile` |
| This record | The spec's §9.9, the daily-loop spec's dated amendments, fixes after review, regenerated catalogs |

The groups share files (`runtime.py` and `host.py` hold both the short path and the job path, and `capture/jobs.py` is in the first
group because `capture/__init__.py` imports it), so a job cannot run until the second commit. Only the tip is gated.

## 0. What moved since the spec was written

Re-checked at `6cf7a91ba8`. `docs/reviews/mobile-pr5-pr7.md` §0 has PR-5..7's table, and each of those still stands. New for M2a:

| Spec citation | At this base | Note |
|---|---|---|
| §6.2 `server.py:48-103` (`_handle`) | `server.py:55` | Still requires `"jsonrpc": "2.0"` and returns None when `id` is absent for `$/` methods only; an id-less ordinary method runs and returns None. The adapter always sends an id |
| §6.2 `errors.py:20-45` | `errors.py:21`, `:38` | Same shape |
| §6.3 `practice.py:489-611` (the submit) | `practice.py:1280` (`submit_attempt_on`) | RW2a's shared body. Grading raises `grading_fallback_required` at `:1421`, `:1464`, retryable |
| §6.6 `practice.py:94-114` (`SubmitAttemptInput`) | `practice.py:177` | No `answer_transcription_id`: M2b's |
| §3.3 `server.py:118-139` | `server.py:228` (`_busy_error`) | |
| §3.1 `repositories.py:778` | `repositories.py:1067` | |
| §3.1 `ai/runtime.py:106` | `ai/runtime.py:107`, `:147` | Provider keys still from the environment |
| §6.6 `ingest/transcription.py:67` | unchanged | M3 |
| §4.5 `tutor_qa.py:231-249`, `:252+`, `tutor/promotions.py:632`, `:640-654` | `handlers/tutor_qa.py:602`, `:623`; `tutor/promotions.py:181`, `:412` | M3 |
| §3.4 "215 commands are `sidecar_passthrough!`" | 399 | The argument holds |
| §3.4 `client.ts:267-279`, `:280+`, `:300+` | `client.ts:395`, `:415`, `:447` | One more shift from PR-5..7's table: this stage adds lines |
| §3.1 `pyproject.toml:123-129` | `:649`, and `mobile-is-independent` at `:673` | **Wrong in substance:** that contract forbade `learnloop_sidecar`, against §3.1's "may import". Amended here |
| §4.5 "`diagnosis_status` once Slice 1 lands" | Landed | On the allowlist |
| §4.5 `adopt_session` "(new, PR-4)" | Registered by PR-6 | Tauri command added here |
| §6.4 "Text cues … logged as `suspected_figure` in the M2 report" | No report existed | Built here, §1 item 5 |
| `spec_daily_loop_v1.md:30`, `:773`, `:885` and `handlers/daily_plan.py:8`: "the phone shows the plan" | Conflict with §4.5 | Amended with dated notes (§1 item 2) |
| §8 `mobile_jobs` columns | As written | Plus an index on `request_id`, which the submission endpoint reads across devices |

**Item kinds, screens and surfaces landed since the spec** were settled by PR-5..7 (`mobile-pr5-pr7.md` §1, §2). The phone changes none.

## 1. The open items from `mobile-pr5-pr7.md`, decided

1. **The host bumps `queue_revision` once at start. Built.** `MobileHost.on_start`, from the ASGI lifespan: after schema checks, before jobs are recovered. A failed bump is logged and the host still starts. Cost: one desktop refetch per host start, and a crash-looping unit restarts at most every 5 s. `test_mobile_host_coexistence` now pins that this is the only row a start writes.
2. **Phone Today is the allowlisted queue, not the stored plan.** §4.5 lists no plan RPC and its record is shared between devices. The daily-loop spec's three lines and `daily_plan.py`'s docstring said otherwise; §4.5 stands and each is amended with a dated note. Because the plan marks an item done by any attempt recorded after it was planned (`daily_plan/engine.py`), a phone's answers still count on the desktop's plan.
3. **A phone offer logs what the phone showed.** `publish_offer`: `head_served = ctx.request_origin is not None or today_head_served(vault)`. The phone shows every row it asks for (`limit`, 20), its head first, and "Next" opens that head. So under a serving plan a phone offer is surface `phone_queue` with an exact propensity, taking the head is no pick, and a row below it is a `learner_pick` on `phone_practice`. A desktop offer under a plan stays `full_list` / `not_served` (test pinned). **One more case found building this:** a diagnostic check the phone commits and does not render stayed the next build's pinned head, so every answer after it would have been logged as a pick the learner never made. The phone's build now holds back that session's committed presentation (`device_filter(..., left_for_desktop=)`), counts it in `device_deferred_count`, and leaves it assigned for the desktop. Phone only; `device_filter` is None for the desktop.
4. **"N items waiting for the desktop"** comes from `device_deferred_count`, on Today. The skip's reply now carries the count too (host origin only), so the line survives a skip with no second build.
5. **`suspected_figure` is a word pattern, and report-only.** `capture/report.py`: a locator and a figure's noun in one sentence ("the graph below"; "Graph the function" is no hit). Detection needs a pattern, so per §6.4 nothing that decides serving reads it. `learnloop-mobile report` lists hits among items offered to or answered on the phone. A test pins that `device_eligibility.py` does not import it. Its misfires cost nothing but a line in a report.
6. **R2's hold is not widened.** It already does what the phone needs. A phone's change reaches Today's list on the next 3 s tick there, and anywhere else is remembered and paid once on the return, so nothing rebuilds per return; `session_moved` is read on every screen. Widening the refetch to other screens would rebuild the plan under an answer being typed, which is what R2 exists to stop. `App.queueRevision.test.tsx` pins one refetch on a phone's change and none on a focus at the same token.
7. **No successor.** The desktop's serving stays byte-identical: its offer path takes no new branch at a None origin (`head_served`, `device_filter`, the reply's keys), `start_session` with no `replace` is the old call, and the frontend sends the same input. No vault has a phone predecessor state, and `practice.device_eligibility_enabled` is the kill switch. The router's inputs on a phone offer name the policy as already built: `device_policy: device_eligibility_v1`, `off` under the switch. No `mvp-0.45`.

## 2. Decisions beyond the brief, for review

- **The host drains the post-attempt queue, from its job context (flagged for the owner).** PR-1 left that queue to the primary. Without this, a phone's diagnosis stays pending for as long as the desktop app is closed, and each phone queue build waits out `next_item_wait_seconds` on a worker with nothing to run (`notify` starts idle threads, so `wait_for` sees a live worker). One `PostAttemptWorker` is shared by both contexts, bound only to the job context, so the RPC context's bounded wait sees the job context's work. The queue is lease-fenced and strict in attempt order across processes, so a desktop beside it runs nothing twice. It spends what the desktop would have spent, under the same budgets, in the host's process, so the host's `mobile.env` needs the same keys. **The prefetch gap trigger stays off** on the host. To remove it, delete the `bind` in `_load_job_context`; then a phone's diagnosis waits for the desktop.
- **A retryable failed job reruns under the same row** (§6.3 amended). Otherwise "retry later" could never work on one submission id. Same hash only; a different one is still 409. The PWA resends the first request's fields exactly and mints a new id if the answer was edited after a failure.
- **`submit_dont_know` takes `submit_attempt`'s constraints, and `probe_presentation_id` is rejected on both.** With that, G10's cap-boundary clause holds by construction for the two host workers: neither can add a qualifying observation. This does not test two contexts committing a presentation at the cap, because the cap counts answers, not presentations.
- **The request log names allowlisted methods** (`rpc:submit_attempt`, §4.6 "endpoint or method"), which is how the report reads the share of submits returning 202. A denied name logs as `/rpc`. Every RPC is logged, draft saves included (at most one per 800 ms of typing, pruned at 90 days); polls are not.
- **`grading_ready` is null until the first RPC** (it was a hard false in M1). A capture-only host has not checked; null says so. It is read off the request path and cached for 60 s, because a route's readiness can start a provider's runtime.
- **The PWA's build is gitignored**, in `src/learnloop_mobile/static/app/`, because KaTeX's fonts and the bundle are build output. `pyproject.toml` lists it as a wheel artifact, `doctor` warns when it is missing, and `/app/` answers 404 until it is built.
- **On iOS an installed app keeps its own storage,** apart from Safari's, so the app pairs itself with the manual code. The pairing page's link (`/app/#token=…`) is for a browser tab. Whether iOS behaves this way on this phone is part of A4.
- **Not on the phone in M2a:** hints, a self-grade, the contest, the A6 explanation line, and `open_queue_item`'s preview (allowlisted, unused). The report's contest rate on phone attempts is therefore 0 by construction until M3 or later, so it cannot yet say what §9 wants it to.

## 3. Known limits

1. **G7's crash recovery is exercised by a second host on rows left as a dead process leaves them,** not by killing a real process mid-grade. `test_mobile_two_process.py` is real processes and WAL, with no kill.
2. **`test_a_restart_with_an_attempt_and_no_receipt…` accepts two outcomes**, `completed` or the typed `submission_committed`, because whether a completion was saved depends on the path. It pins one attempt, no second grade and no hang, not which end.
3. **The editor and the symbol bar were never run on iOS.** §3.4 calls for touch and IME testing on Safari; jsdom has no `execCommand`, so vitest covers only the append fallback. Part of A4. **The screens have never been rendered in any real browser**: no browser window, by the stage rule.
4. **`createImageBitmap`, the canvas re-encode and a real Blob through IndexedDB are untested** (jsdom and the fake IndexedDB cannot do them). The multipart request is tested from a Blob directly. Part of A4.
5. **Starting fresh from the phone when a job is still running on the replaced session** fails that job with `session_ended`, typed. The answer stays on the screen that sent it, not in `session_handoffs` unless a draft was saved first (it always is, before a submit).
6. **`suspected_figure` has never seen a real prompt** beyond the test list.
7. **PR-4's open list stands** (§9.5: "the workbench, tutor and Ask, daily-plan and other session-keyed writes outside practice"). The desktop can still make those writes on a session a phone holds: `next_plan_item` with a session, for one. The phone cannot reach them, the banner is up by then and the practice screen is frozen, and the answer that would follow is refused, so the realistic harm is a plan presentation bound to a session that moved. Not closed here.
8. **`mobile_jobs` keeps each job's params, answer included, with no pruning.** §8 and §4.6 prune only the request log. Learner text is not private by the owner's rule, and the table grows by one small row per phone submit.

## 4. Persisted and served meaning

Migration 240 adds one workflow table, never evidence; replay ignores it. New `mobile_request_log` labels only. No new config key, no parameter-registry key and no model constant. The numbers added are operational bounds, each with its reason beside it: `JOB_WAIT_SECONDS` (15, §6.3), `RPC_QUEUE_LIMIT` and `JOB_QUEUE_LIMIT` (16 and 8, §4.6), `MAX_BOOTS` (3, §6.3), `READINESS_TTL_SECONDS`, the `LANE_LIMITS`, and in the PWA the polling intervals, `PHONE_QUEUE_LIMIT`, the retry bound and the image's edge.

## 5. Gates G1-G12

| Gate | Where | State |
|---|---|---|
| G1 | `test_mobile_host_auth` | M1's, unchanged |
| G2 | `test_mobile_host_auth`, `test_mobile_rpc` (the new endpoints, the shell) | Through fakes; A1, A2 for the real path |
| G3 | `test_mobile_allowlist`, `test_mobile_rpc` (enumerates the registry over HTTP; each constraint) | Pass |
| G4, G5 | `test_mobile_capture`, `test_capture_*`, `test_mobile_pairing` | M1's, unchanged |
| G6a | `test_mobile_host_coexistence`, `test_synthesis_sweep_primary_only` | Pass. A start now writes one bump |
| G6b | `test_mobile_two_process`: real processes, WAL, a primary desktop, a running content sync, a leased job left alone | Pass. Two workers on two contexts: `test_mobile_rpc`, `test_mobile_jobs` |
| G7 | `test_mobile_jobs` | Pass. Crash recovery from rows, not a killed process (§3) |
| G8 | M2b's: `answerTranscriptionId` is refused (`test_no_parameter_can_set_the_origin`) | **Not applicable to M2a,** though the §9 row names G1-G12 |
| G9 | `test_device_eligibility`, `test_mobile_rpc`; `App.test.tsx` for the client's probe rule | Pass. Desktop reply pinned at a None origin |
| G10 | `test_session_ownership`, `test_mobile_handoff` | Pass. Cap boundary by construction (§2) |
| G11 | `test_request_origin`, `test_mobile_rpc` | Pass |
| G12 | `test_mobile_rpc` (YAML, with the 2 s window opened by hand), `test_host_queue_revision`, `App.queueRevision.test.tsx` | Pass |
| A1-A4 | §7 | **Not run: the owner's** |

## 6. Gate (this step; the full suite runs once in the landing gate)

Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` and only `UV_CACHE_DIR`, `CARGO_HOME` and the npm cache pointing at real caches; pytest at `-n 6`, one at a time, the large set behind `flock /tmp/learnloop-fullsuite.lock`. Run on the tree this record is added to; only this record and its test list follow.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **42 kept, 0 broken** |
| **Targeted set**, 248 files, `docs/reviews/artifacts/mobile-m2a-targeted-tests.txt`: every test file this stage added or changed (65, the head-fixture rename among them), PR-5..7's 191-file list (every file naming a function or module these stages touch), and the contract tests (architecture, CLI help and config defaults where present, desktop RPC contract, serializer snapshot, sidecar contract, mobile allowlist, table roles, coordinated migrations, tracked fixture databases, public tip guards, module catalog inventory, secondary attach) | **5,037 passed, 35 skipped, 0 failed**, 36 min |
| Durability lane (`-m durability`): `test_mobile_two_process`, `_host_coexistence`, `test_host_queue_revision`, `test_request_origin`, `test_device_eligibility`, `test_session_ownership`, `_migration`, `test_attempt_content_state_race`, `test_secondary_attach`, `test_synthesis_sweep_primary_only` | **241 passed** |
| `--durable-sqlite`: `test_mobile_jobs_migration`, `test_mobile_handoff`, `test_mobile_jobs` | **48 passed** |
| Desktop: `npm install`, `typecheck` | clean |
| Desktop vitest: `src/app/`, `src/api/`, `src/render/`, `src/screens/TodayScreen*`, `screens/today`, `StartScreen*`, `PracticeScreen*` | **534 passed**, 53 files |
| Desktop `frontend:build` | ok |
| Phone: `npm install`, `typecheck` | clean |
| Phone vitest (`apps/learnloop-mobile`, all) | **69 passed**, 6 files |
| Phone `npm run build` | ok; output gitignored |
| `cargo check` | clean (`adopt_session`) |
| `db_generate_reference`, `db_validate_reference` | errors `[]`, 374 table notes, head 240 |
| `desktop_generate`, `desktop_validate` | 317 TS and 6 Rust notes; valid, pins updated (317; 306 entry-reachable; 323 active) |
| `module_generate`, `module_validate`, `validate_vault` | 1,158 module notes; 2,117 notes; valid |

**Not run here, by the owner's rule:** the full suite, the whole durability lane, the whole vitest run. **Never run at all:** a real browser, a real phone, Tailscale, any provider.

**The first targeted runs did catch things:** a blanket `.gitignore` `lib/` was silently dropping `apps/learnloop-mobile/src/lib`, so the app moved to `src/util`. An early commit also carried `apps/learnloop-mobile/node_modules`, whose ignore rule named only the desktop's; it was unwound before any further commit, and the guards pass now. **That left a dangling commit** in the shared object store, about 33 MB loose, never on a branch; `git gc` reclaims it, and it was not run here because the store is shared with every worktree.

**Main moved during this stage:** `42aeeec9ec` (the mobile HTTPS port) landed on main, touching `host.py`, `config.py`, `cli.py`, `doctor.py` and this spec. Not merged here, by the stage's "don't merge" rule, since its exception names the data-capture stage only. `git merge-tree` against it reports **no conflicts**, but the merged tree has not been tested. M2a's own URLs are all relative (the PWA, its manifest and the service worker), and main's `https_authority` and `base_url` cover the host's checks and the pairing link, so M2a has nothing of its own to change, as that spec section asks.

## 7. What the owner runs on the phone (A1-A4)

Nothing below has been run. Set up on carson first, once this has landed and the vault is upgraded (open the desktop app once):

```bash
cd ~/Documents/thinking/learnanything
uv sync --extra dev --extra mobile && uv pip install pypdfium2
(cd apps/learnloop-mobile && npm install && npm run build)

mkdir -p ~/.config/learnloop ~/.config/systemd/user
cp deploy/mobile.toml.example ~/.config/learnloop/mobile.toml   # set enabled = true, vault, hostname, owner_login
cp deploy/mobile.env.example ~/.config/learnloop/mobile.env && chmod 600 ~/.config/learnloop/mobile.env   # the grading keys
cp deploy/learnloop-mobile.service ~/.config/systemd/user/      # set ExecStart to this checkout's .venv
systemctl --user daemon-reload && systemctl --user enable --now learnloop-mobile
# Main's 42aeeec9ec added https_port to mobile.toml: use the same port here if 443 is taken.
tailscale serve --bg --https=443 http://127.0.0.1:8765
.venv/bin/learnloop-mobile doctor
```

Below, `HOST` is the hostname in `mobile.toml`, with `:port` when `https_port` is not 443.

- **A1. Serve strips a forged identity, and the host sees the real login.** From the phone or another tailnet device:
  ```bash
  curl -s -o /dev/null -w '%{http_code}\n' -H 'Tailscale-User-Login: someone@else.example' https://HOST/pair   # 200: Serve replaced it with yours
  curl -s -o /dev/null -w '%{http_code}\n' https://HOST/api/v1/status                                           # 401: no token
  ```
- **A2. Only the expected mapping, and nothing off the tailnet.** On carson, `tailscale serve status --json` shows the configured HTTPS port to `http://127.0.0.1:8765`. With Tailscale off on the phone, on cellular, opening `https://HOST/healthz` must not connect.
- **A3. The Shortcut (M1's, still pending).** `.venv/bin/learnloop-mobile pair --label "Shortcut" --scope capture`, paste the token into the Shortcut's setup. Disconnect Tailscale, share something to the Shortcut (VPN On Demand should connect). Then `systemctl suspend` on carson, capture again (the outbox holds it), wake carson, run "Flush LearnLoop outbox", and check `.venv/bin/learnloop-mobile inbox list`.
- **A4. The app.**
  1. `.venv/bin/learnloop-mobile pair --label "iPhone" --scope app`, and note the manual code.
  2. In Safari open `https://HOST/app/`, then Share, Add to Home Screen. Open it from the home screen and enter the code.
  3. **Offline capture:** `systemctl suspend` on carson. In the app, open Capture, save a note and a photo; it says "Desktop offline" and the count. Wake carson, reopen the app, and check `inbox list`.
  4. **A submit backgrounded mid-grade:** Today, 10 min, Next, type an answer (try the symbol bar and `$x^2$`), Submit, then leave the app at once for over 20 s. On return the feedback is there. `.venv/bin/learnloop-mobile report` then shows the submit.
  5. **Handoff, with the desktop app open:** start a session on the desktop, then Begin on the phone: it asks; choose "Continue it here". The desktop shows "This session continued on iPhone" within about 3 s; "Take it back" returns it with the phone's draft. Then the other way: with the phone's session open, Begin on the desktop asks the same.

Reports for §9's row: `.venv/bin/learnloop-mobile report`, read-only.

## 8. Open questions

1. Should the host keep draining the post-attempt queue (§2)? It is the one thing here beyond the spec that spends money from a new process.
2. §3 item 7: should PR-4's remaining session-keyed writes be closed before the owner uses a phone daily, or left as Low?
3. The contest rate in the report is 0 by construction until the phone has a contest (§2). Is a phone contest wanted before M3?
4. Main's `42aeeec9ec` is not merged here (§6). The landing merges it, and that merged tree is what the gate has to test.
5. Landing: 239 and 240. Whichever lands second renames the head fixture and reruns `db_generate_reference`, which takes about 4 minutes. A mechanical rename across 59 files is what moved 238 to 240 here.
