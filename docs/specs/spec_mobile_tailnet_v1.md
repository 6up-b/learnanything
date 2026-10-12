# Phone capture and a small mobile client over the tailnet (v1)

**Status:** revision 4 (2026-10-12).
- **M1 is built** on branch `mobile/m1` (9c3e431f), with automated checks green.
- **Phone acceptance A1–A3 is pending.**
- **M2 and later are not built.**

**Revision 4 (2026-10-12, owner): the spec follows the M1 build.** M1 was implemented with revision 2's pairing exchange and token scopes, and the owner chose to keep them. So:
- §4.2 and §4.3 are restored to pairing plus scopes.
- D16 is reinstated.
- §3.1, §9, G5 and the test list match the build.
- An "As built (M1)" section records the implementation decisions (§9.1).

Revision 3's other decisions stand: iOS only, no LearnLoop-specific tailnet policy, and `doctor` checking Serve, Funnel and loopback.

**Revision 3 (2026-10-11, owner): sized for a single-user tailnet.** The tailnet is the owner's alone: `carson` (this desktop), `iphone-13-pro-max`, `mimas` and `minty`, all under one login. The owner wants general phone → desktop access over it (SSH and other services), so reachability is a tailnet matter, not a LearnLoop one. The changes:
- **No LearnLoop-specific tailnet policy.** The phone-only grant, the "remove broad rules" step and the policy tests are gone (D12). Every device on the tailnet is the owner's.
- ~~**Pairing is one command.**~~ Superseded by revision 4: M1 kept the pairing exchange (§4.2).
- ~~**One token scope.**~~ Superseded by revision 4: M1 kept the capture and app scopes (§4.3, D16).
- **iOS is decided** (D1). The iPhone is the phone. The Android share target is dropped; the Shortcut is the capture path.
- **`doctor`** checks Serve, Funnel and loopback, and no longer asks the owner to confirm a policy (§4.7).
- **Stale confirm-step text** from revision 2 is fixed (§4.4, §11).

**Revision 2 (2026-10-11)** folds in an adversarial review (Claude, plus a Codex reviewer) that checked every code citation. The main changes:
- **M1 is now a narrow capture service.** It no longer loads a `SidecarContext`, because loading one is never passive (§3.1).
- **The "read lane" is gone.** It is replaced by read-only status endpoints and a secondary attach mode (§3.1, §3.3).
- **Long mutations become durable jobs.** Submits, clarification answers and tutor asks are accepted as jobs with a typed terminal state, so the phone never sees "pending forever" (§6.3).
- **Session handoff is atomic.** It uses a compare-and-swap on the open session plus an ownership check on session-scoped writes (§6.5).
- **Transcribed answers bind a specific revision** to each grading, and the server derives the graded text from it (§6.6). *Revised 2026-10-11 (owner, frictionless defaults):* there is **no confirm step before grading**. The answer is graded immediately on the transcript, the transcript is shown beside the grade, and one tap corrects a misread and regrades.
- **HTTP stack decided (D3):** Starlette + uvicorn + `python-multipart` in a `mobile` extra (§3.1).
- **An explicit HTTP↔JSON-RPC adapter** (§6.2), an endpoint authentication matrix (§6.1), hardened pairing (§4.2), token scopes (§4.3) and browser/HTTP limits (§4.6). *Pairing and scopes were simplified away in revision 3.*
- **Prerequisite changes to shared code** are now listed and gated (§3.3, §9). They cover vault-state sync, the abandoned-synthesis sweep, request origin, device eligibility, and desktop freshness.
- **Citation corrections.** MathLive is not a dependency. The originals store lives in `ingest/originals.py`. Attempts do not bump `queue_revision`. Tutor promotion can route to review.

**Owner framing (2026-10-11):**
- The phone and this computer are on the same tailnet. Use that instead of public exposure or a cloud relay.
- The tailnet is single-user, and the phone has general access to the desktop over it anyway (revision 3). LearnLoop does not narrow tailnet access.
- Learner text going to model providers is acceptable. The LearnLoop server itself must be reachable **only inside the tailnet**.
- Phone capture comes first. It then grows into a small mobile LearnLoop: sessions, practice Q&A with feedback, and tutor Q&A. **No reader in this version.**

**Depends on, and does not decide:** the daily-loop open questions Q0–Q18 listed in chat on 2026-10-11. They are unanswered. Every place this spec leans on one names it (§6.7, §12). The relevant ones are:
- Q1 capture semantics;
- Q2 topic choice at capture;
- Q3 who writes the answer;
- Q4 channel order;
- Q6 intent at capture;
- Q9 finite plan vs open list;
- Q14 readiness form;
- Q16 grading latency;
- Q17 auto-advance.

**Relationship to other documents:**

| Document | Relationship |
|---|---|
| `spec_image_dropin_ingest.md` (proposed, not built) | Its photo → transcript → *mandatory review* → item pipeline is the processing path for photo captures. Its §1 put "mobile and share sheet" out of scope; this spec is that missing transfer leg. Its `image_transcription` route is a prerequisite for photo **answers** (M2b), not for typed practice (M2a) |
| `spec_blind_grading_diagnosis_split_v1.md` (proposed, not built) | Independent of this spec. Phone answers reach whichever grader is live as the bound transcript text (§6.6). If Slice 1 has landed, that is `BlindGradingContext`; if not, it is the current grader's `learner_answer_md`. Slice 1's `diagnosis_status` joins the allowlist when it exists |
| `spec_project_understanding_v1.md`, `spec_embedding_consumers_v1.md` | No dependency. The phone can later serve their items like any other |

---

## 0. Thesis

**Capture is the gap.** The audit of 2026-10-11 found that every capture path starts inside the desktop app and needs an existing subject or topic. Nothing works away from the desk, yet the intentions doc's first examples are things met in the wild: "math problems I see that are difficult to me", "concepts from arxiv papers". The cheapest fix that keeps LearnLoop local-first is not a cloud service. It is the owner's existing tailnet:
- an HTTPS endpoint on the desktop, served by `tailscale serve`;
- reachable only from the owner's devices;
- fed by the phone's share sheet.

**A small mobile client follows.** Once that endpoint exists, a phone client for the daily loop uses the same plumbing with a narrow RPC allowlist. Short sessions in idle minutes are where retrieval practice fits a life, and the scheduler already runs on the desktop. The phone renders, answers and asks; the desktop decides, grades and stores.

**What the phone is not.** It is not a second LearnLoop. It holds no learner state beyond:
- its credential;
- an outbox, including captured media awaiting upload;
- a cached session snapshot;
- the media of answers awaiting their grade.

Every decision and every durable write happens on the desktop, in the same Python domain code and the same `state.sqlite`.

---

## 1. Scope

**In scope:**
- **P1.** A headless **LearnLoop mobile host** (`learnloop-mobile serve`). It serves HTTP on `127.0.0.1` behind `tailscale serve`, independently of whether the desktop app is open. In M1 it is a narrow capture service that attaches to the database without migrating and runs no sidecar machinery. From M2 it adds a practice runtime in *secondary attach* mode (§3.1).
- **P2.** Device pairing, scoped per-device tokens, a Tailscale identity check, and a default-deny RPC allowlist with per-method parameter constraints (§4).
- **P3.** A capture endpoint and a durable inbox (§6.1, §6.7), fed by an iOS Shortcut. The desktop can see the inbox and route its entries.
- **P4.** A mobile web client (PWA) for Today, practice, feedback and tutor Q&A (§3.4, §5).
- **P5.** Answering on a phone:
  - by typing (Markdown plus LaTeX; M2a);
  - by photo of a handwritten answer (M2b);
  - by voice (M3).

  For photo and voice, the answer is graded immediately on its transcript. The transcript is shown with the grade, and one tap fixes a misread and regrades (§6.6).
- **P6.** Offline capture: the phone queues captures, including their media, and syncs them later (§7).

**Out of scope:**
- **The reader**, including PDF and `llpdf://` viewing, highlights and section progression.
- Ingest administration, settings, AI provider keys, SQLite admin, and arbitrary vault file operations. These are never reachable from the phone (§4.5). Two allowlisted M3 methods write vault files at server-chosen paths. They are named exceptions (§4.5), not a general file capability.
- **Diagnostic probe interaction on the phone in M2.** The phone still commits the serve event, as the desktop does (§6.4).
- **Audio capture in M1.** No manual route exists for it; audio arrives with voice answers in M3.
- Offline practice with immediate feedback (§7).
- Tailscale Funnel or any public exposure.
- Tailnet access policy. The tailnet is the owner's alone, and narrowing it is not LearnLoop's job (D12).
- Android, including the PWA share target (D1).
- Multi-user use, and more than one phone in a single session at a time.
- A native app store build. Tauri 2 mobile is an option, not v1 (§5).

---

## 2. Standing constraints

Inherited unchanged: plan invariants, the authority model of `spec_causal_attribution_v1.md`, and `CLAUDE.md`'s migration procedure. Slice 1's S1–S7 apply once Slice 1 lands. In addition:

- **T1. One source of truth.** The phone never writes learner state locally beyond what §0 lists. Every durable write goes through shared domain code on the desktop:
  - registered sidecar handlers (`src/learnloop_sidecar/registry.py`, `METHOD_REGISTRY`) for RPC;
  - the capture module (`src/learnloop/capture/`, new) for the non-RPC capture and media endpoints.

  The host never writes SQL of its own beyond the mobile tables in §8.
- **T2. Tailnet-only, honestly bounded.**
  - The host binds loopback only.
  - Exposure is through Serve, never Funnel.
  - Each API request carries a valid device token, and Serve's identity header must name the owner.

  **Trust boundary:** the tailnet is single-user, so every device on it is the owner's. The token mainly identifies *which* device is calling, for session ownership and provenance (§6.5, §6.8). It also keeps the API closed if a node is ever shared with someone else. Code running as the owner's desktop user can read the vault directly, and nothing here defends against that (§4.1).
- **T3. Default-deny RPC.** The phone can call only methods on an explicit allowlist that lives in code, with per-method parameter constraints. A newly registered sidecar method is unreachable from the phone until it is added there (§4.5).
- **T4. The grader grades exactly the bound transcript revision.** A photo or voice answer is transcribed and graded immediately on that transcript (revision 0). If the learner corrects a misread afterwards, the correction becomes a new revision with a new grading epoch through the existing regrade path. Every grade names the revision it graded (§6.6).
- **T5. No new evidence semantics.** A phone attempt is an ordinary attempt. Its surface goes in the existing `entry_surface` field, and its modality is recorded through the transcription binding (§6.8). Neither weights evidence in this spec.
- **T6. Capture semantics follow the daily-loop defaults** (`docs/specs/daily_loop_frictionless_defaults.md`, decided 2026-10-11).
  - **Saving makes a reference; no practice begins.** Filing under topics, and solving and verifying a captured problem, happen in the background with no question to the learner.
  - **One tap adopts it into practice.** The phone shows "Practice this" on the capture's receipt and in the inbox.
  - **Staging.** M1 still only receives and stores captures, with manual routing on the desktop (§6.7). The background processor arrives in M3.
- **T7. The host is a secondary process.** It never migrates the schema, runs startup maintenance, refreshes the canonical projection, schedules cold probes, or sweeps abandoned synthesis runs. The desktop app and the `learnloop` CLI remain the primary hosts (§3.3).
- **T8. Request origin comes from the server.** The device and surface of a request come from the authenticated token, carried on the handler context. They are never accepted from request parameters (§6.8).

---

## 3. Architecture

```
phone (iOS Shortcut / PWA)
   │  HTTPS  https://<desktop>.<tailnet>.ts.net/        (tailnet only; WireGuard)
   ▼
tailscaled on the desktop ── tailscale serve --bg --https=443 http://127.0.0.1:<port>
   │  adds Tailscale-User-Login / -Name / -Profile-Pic; strips client-sent copies
   ▼
learnloop-mobile serve  (127.0.0.1:<port>; systemd --user service; package learnloop_mobile)
   ├─ edge: Host/Origin check → identity check → token check → limits   (§4)
   ├─ /app/*                 identity-gated, no bearer (static shell only)
   ├─ /api/v1/capture …      → learnloop.capture (capture_inbox, originals store)   [M1]
   ├─ /api/v1/…/status       → read-only Repository.attach                           [M1+]
   ├─ /rpc  {method, params} → adapter (§6.2) → RPC worker   (SidecarContext #1, secondary)
   │                                         → job worker   (SidecarContext #2, secondary) [M2+]
   └─ /app/                   static PWA build (apps/learnloop-mobile)
        │
        ▼  same vault: state.sqlite (WAL, synchronous=FULL, busy_timeout) + vault files
desktop app (Tauri) ── its own sidecar process (stdio JSON-RPC), the primary host
```

### 3.1 The host process

**Packaging.**
- The host lives in a new package, `src/learnloop_mobile`, with its own console script, `learnloop-mobile`. Its subcommands are `serve`, `pair`, `devices`, `revoke`, `inbox list` and `doctor` (as built).
- `learnloop.cli` may not import `learnloop_sidecar`. The `entry-points-are-independent` import-linter contract forbids it (`pyproject.toml:123-129`).
- `learnloop_mobile` is added to that contract as another independent entry point. It may import `learnloop` and `learnloop_sidecar`; nothing imports it.
- Inbox listing for the desktop user is also exposed as `learnloop inbox list`, through `learnloop.capture`.
- `pyproject.toml` adds the script and the package to the wheel's `packages`.

**M1: capture service only.**
- **Attach.** It attaches with `Repository.attach(sqlite_path)` (`db/repositories.py:778`), which applies no migrations.
- **Schema check.** It refuses to start unless the schema is at the version this code expects. On mismatch it exits with status 78, and the systemd unit sets `RestartPreventExitStatus=78`. `doctor` then explains "open the desktop app or run `learnloop doctor --vault …` once to migrate".
- **What it writes.** Only the capture and device tables, and capture media through `learnloop.ingest.originals.store_original_bytes` (§6.7).
- **What it never loads.** No `LoadedVault`, no `SidecarContext`, no ingest runner.

**M2: practice runtime in secondary attach mode.**
- **New entry point.** `SidecarContext.load_secondary(vault_path, *, bind_ingest=False)` (new) attaches without migrating, and loads `LoadedVault` for reading. It runs **none** of what `load()` does today (`context.py:45-80`):
  - `sync_vault_state` (§3.3, PR-2);
  - `refresh_canonical_projection_on_startup`;
  - `schedule_certification_cold_probes`;
  - `run_startup_maintenance`;
  - ingest binding and `recover_stale_leases`.

  It is not a read-only mode: handlers called on it write as usual. It only does no startup work.
- **Two workers, each owning one context.** No context is ever shared between threads; HTTP threads only enqueue and wait.
  - **RPC worker:** a thread that owns SidecarContext #1. It executes short allowlisted RPCs in arrival order.
  - **Job worker:** a thread that owns SidecarContext #2. It executes long mutations as durable jobs (§6.3): `submit_attempt`, `submit_dont_know`, `answer_grading_clarification`, transcription, and in M3 `ask_tutor_question`. A 60–180 s grade therefore never blocks a short RPC.
- **Same as two processes.** The two contexts relate to each other exactly as two processes do today. SQLite serializes writes, the completion lock (`attempts/completion_lock.py`) serializes post-attempt completion, and the vault mutation lock (`vault_lock.py`) serializes YAML writes. That is the arrangement G6b tests.
- **Ingest runner.** In M3 only, the job worker binds an ingest runner restricted to the question-promotion job types, so a promotion drains while the desktop is closed. Its worker id is `mobile-host-<pid>`. It runs expired-lease fencing only, never `_finalize_abandoned_synthesis_runs_locked` (§3.3, PR-3).

**Status reads.** Capture status, job status, transcription status, submission status and the queue revision are served from `Repository.attach(sqlite_path, read_only=True)`. They never go through a sidecar handler, so they cannot reload, resume completions, or block on the completion lock.
- In particular, the sidecar's `recover_practice_submission` is **not** a status read. It can resume a committed attempt's completion, which includes a provider call and up to 120 s waiting on the completion lock (`practice.py:687-737`, `completion_lock.py:27`).
- Likewise `get_queue_revision` is not a status read, because it can call `ctx.reload()` (`queue.py:53-71`).

**Content freshness.**
- Before each RPC or job, the worker compares `vault_content_fingerprint(root)` with the fingerprint its context loaded. `vault_content_fingerprint` is new and lives next to `load_vault`, so the file set it covers cannot drift from the set the loader reads. It combines the file count and the newest `mtime_ns` over that set, and is cached for at most 2 s.
- On a mismatch, the worker reloads its own context with `load_secondary`.
- A request already running finishes against the version it started with, as the desktop does today.
- The database is never fingerprinted by mtime: WAL makes that meaningless, and database state is read fresh on every connection (`repositories.py:801`).

**Supervision.** A `systemd --user` unit starts the host at login and restarts it on failure, except on status 78.
- `TimeoutStopSec=300`. On SIGTERM the host stops accepting work, lets the running job finish, and leaves queued jobs durable for the next start.
- Provider keys come from `EnvironmentFile=%h/.config/learnloop/mobile.env` (mode 0600). The unit does not inherit shell environment variables, and `ai/runtime.py:106` reads provider keys from the environment.

**HTTP stack (D3, decided 2026-10-11): Starlette + uvicorn + `python-multipart`.**
- **Packaging.** They ship in a new `mobile` optional extra in `pyproject.toml`, with exact versions pinned when M1 lands. The host is installed with `uv sync --extra dev --extra mobile`. `learnloop_mobile` imports them, and nothing in `learnloop` or `learnloop_sidecar` does.
- **Why not the standard library.** It has no multipart parser (`cgi` is deprecated), no enforcement of request size or read deadlines, and only basic security checks.
- **One server process.** uvicorn runs with `workers=1`, `host="127.0.0.1"` and `proxy_headers=False`. Serve is the only proxy, and the identity check reads Serve's headers directly. The `Host` check is the first middleware.
- **The event loop never runs handler code.** Endpoints are `async def`. They put work on the RPC or job worker queue (§3.1) and await the result through `asyncio.wrap_future`, with the 15 s wait in §6.3 as `asyncio.wait_for`. A client disconnect cancels only that await, never the worker.
- **Limits are still ours to write.** Starlette and uvicorn do not impose §4.6's limits by default, so the host adds them:
  - an ASGI middleware enforces the header, body and media caps by counting received bytes before any parsing;
  - multipart is parsed with `request.form(max_files=1, max_fields=10)` plus a per-part size cap;
  - uvicorn's `limit_concurrency`, `timeout_keep_alive` and `h11_max_incomplete_event_size` cover connection-level limits;
  - the 60 s body read deadline is enforced in the middleware.
- **Static assets** are served with Starlette's `StaticFiles` from the packaged app directory, with `follow_symlink=False` and no directory listing.

### 3.2 Network path: Tailscale facts this design relies on

Verified against Tailscale documentation on 2026-10-11; see the References.

- **Tailnet-only HTTPS.** Serve "lets you route traffic from other devices on your Tailscale network" to a local service, at `device-name.tailnet-name.ts.net`, with TLS certificates provisioned for that name. Serve requires HTTPS certificates to be enabled for the tailnet. [Serve]
- **Persistent configuration.** `tailscale serve --bg …` "runs persistently in the background until you disable it" and resumes after reboot or `tailscale down`/`up`. Use `tailscale serve status [--json]` to check it, and `tailscale serve --https=443 off` or `tailscale serve reset` to remove it. The proxy note says "only `http://127.0.0.1` is supported for proxies." [Serve CLI]
- **Identity headers.** Serve adds `Tailscale-User-Login`, `Tailscale-User-Name` and `Tailscale-User-Profile-Pic` to proxied requests and strips client-sent copies. The headers are "not populated for traffic originating from tagged devices" and are absent for Funnel traffic. Serve's documentation recommends that the backend listen only on localhost. That *limits* header forgery to local processes; it does not prevent it. [Serve]
  - **Consequence:** the phone must stay a **user-owned (untagged)** device. The desktop *may* be tagged, because the headers describe the source.
  - **Consequence:** in a single-user tailnet every device carries the owner's login, so the identity check only matters if a node is shared with another user. It is one string comparison and stays. The token identifies the device (T2).
- **Funnel stays off.** Funnel "is disabled by default" and needs a `funnel` node attribute in the policy file. A port's visibility follows the most recent command: if that was `serve`, "the port will be completely private." Funnel traffic also carries no identity headers, so the host would reject it anyway. [Funnel]
- **Access control.** ACL and grant rules apply to Serve. The owner's tailnet keeps its existing policy: the phone has general access to the desktop, and LearnLoop does not narrow it (D12). [Serve; Grants]
- **The host never sees the phone's tailnet IP,** because Serve proxies from loopback. Tokens are therefore application credentials, not device-bound ones.
- **iOS.** VPN On Demand can bring Tailscale up automatically when iOS connects to a `*.ts.net` hostname, so a share-sheet Shortcut works without opening the Tailscale app first. Hostname matching requires the interface rule to be **Do Nothing**. [VPN On Demand]
- **Sleep and offline (general networking, not doc-verified).** A sleeping or offline desktop is unreachable, because the tailnet has no store-and-forward. §7 designs for this.

**Why loopback behind Serve, and not `0.0.0.0` or the Tailscale IP:**
- **`0.0.0.0`** would also listen on LAN and café Wi-Fi interfaces.
- **The Tailscale IP directly** gives plain HTTP, which is encrypted by WireGuard but is not a secure context. Browsers require HTTPS for service workers, so there would be no PWA install and no offline outbox. There would also be no identity headers.
- **Loopback behind Serve** gets a real certificate, identity headers stripped of spoofed copies, ACL enforcement, and no LAN exposure.

### 3.3 Two processes, one vault

**What already holds across processes:**
- **SQLite.** Migration puts the vault in WAL (ADR-015). Every connection sets `synchronous=FULL` and `busy_timeout` (`db/connection.py:105-114`). Concurrent writers serialize. A lock that outlasts the timeout surfaces as the retryable `database_busy` (`server.py:118-139`).
- **Attempt idempotency.** The unique submission index (`migrations/053_attempt_submission_idempotency.sql`) gives **one committed attempt per submission id**. The concurrent-winner path in `submit_attempt` returns the winner's receipt (`practice.py:587-594`), and the completion lock serializes completion. Two callers can still both pay for a grade before one loses the insert race; §6.3 coalesces this inside the host.
- **Vault files.** YAML writers take `vault_mutation_lock`. The desktop's Rust watcher dispatches changes to `refresh_vault_files` (`src-tauri/src/vault_watcher.rs:106`). The host uses the content fingerprint (§3.1).

**What does not hold today. These are prerequisites, landed and gated before the M2 host (§9):**
- **PR-1. Secondary attach.** Add `SidecarContext.load_secondary` (§3.1), plus a unit test that it performs no writes during attach.
- **PR-2. Content sync never restores stale scheduling state.**
  - `sync_vault_state` snapshots item states (`substrate/state_sync.py:77`). When an item's content hash or active flag changed, it writes back the *snapshotted* difficulty, stability, retrievability, due date and last-attempt time (`:113-123`). An attempt committed in between is overwritten.
  - Change: the update branch issues a targeted `UPDATE` of `active` and `content_hash` only. This is a correctness fix for the desktop and TUI as well.
- **PR-3. The abandoned-synthesis sweep belongs to primary hosts only.**
  - `_finalize_abandoned_synthesis_runs_locked` (`content/pipeline/runner.py:648-665`) treats leaseless synchronous synthesis runs older than the lease cutoff as abandoned. Its own docstring says synchronous RPC and CLI runs have no lease.
  - Change: `bind(…, sweep_abandoned_synthesis=False)` for secondary hosts, and the host never calls it. Durable ownership for synchronous synthesis is out of scope here.
- **PR-4. Atomic session operations and ownership** (§6.5).
- **PR-5. Request origin on the context** (§6.8).
- **PR-6. Device eligibility module** (§6.4).
- **PR-7. Desktop freshness.**
  - Attempts do not bump `queue_revision`: it is an explicitly maintained counter with no trigger (`repositories.py:4621`, `migrations/117_question_promotion_jobs_and_queue_revision.sql:101`). The desktop polls it only while Today is mounted (`TodayScreen.tsx:341-360`).
  - Change: the host bumps `queue_revision` after each committed mutation that changes what the desktop shows: job completion, skip, and session start, adopt or end.
  - The desktop moves the revision poll to app level, adds a refetch when the window regains focus, and on a revision change also re-reads its open session, to detect `session_moved` (§6.5).
  - Desktop-originated writes keep today's behaviour.

**Gate ordering.** M1 already runs a second process against the vault, so G6a (host coexistence, §10) gates M1. The full two-process gate G6b gates M2.

### 3.4 The mobile frontend: what transfers from the desktop app

**The transport is swappable, through an adapter.**
- Every desktop request goes through one function, `call(command, args)` in `apps/learnloop-tauri/src/api/client.ts:267-279`, which wraps Tauri `invoke`.
- On the Rust side, 215 commands are `sidecar_passthrough!` macros forwarding `input` unchanged to the same-named method (`src-tauri/src/commands.rs:65-75`). Most hand-written commands only rename one argument into `{"sessionId": …}`-style params (`commands.rs:127-200`).
- The mobile `call()` posts `{method: command, params: args.input ?? args}` to `/rpc`. It turns the host's error body into the same `CommandError` shape that `normalizeError` produces (`client.ts:280+`), and treats `202 accepted` as a job to poll, not as a result (§6.2, §6.3).
- The `dto.ts` types, the query cache and the mutation-tag invalidation (`client.ts:300+`) carry over.
- Mutation wrappers whose DTO is a final result, such as `submitAttempt → AttemptResultDto`, get mobile variants that return `Accepted | Result`.

**The screens do not transfer well.**
- `components/ui.tsx:2-3` imports `@tauri-apps/api/window` and `@tauri-apps/plugin-dialog` at module scope; `src/app/App.tsx:1` listens to Tauri events; `FeedbackScreen.tsx:999` uses the opener plugin.
- The target screens are large desktop, keyboard-first layouts: Today is 1,698 lines, Practice 1,615, Feedback 2,624, AskOverlay 768.
- Shimming Tauri and making those layouts responsive would cost more than writing a few small phone screens, and would tie phone UX to desktop UX.

**Recommendation (D4):** a separate Vite app, `apps/learnloop-mobile`. It:
- imports `apps/learnloop-tauri/src/api/dto.ts`, the query cache and tags, and the render components `render/MarkdownMath.tsx` and `render/MathLiveEditor.tsx`;
- has its own HTTP `call()`;
- has five screens: Capture, Today, Question, Feedback and Ask.

The host serves its build at `/app/`.

**Math input, accurately.** `render/MathLiveEditor.tsx` is a KaTeX-rendered `contentEditable` Markdown/LaTeX editor. It does not import MathLive, and MathLive is not a dependency.
- M2a ships that editor with plain LaTeX entry and a small symbol bar of common commands, tested on iOS Safari for touch and IME behaviour.
- A real math keyboard (MathLive or similar) is a later, separately budgeted item. Photo answers (M2b) are the main route for symbol-heavy work.

**Remote resources.** On mobile, `MarkdownMath` renders remote images as links, not `<img>`, to match the CSP in §4.6.

---

## 4. Security and privacy

### 4.1 Layers and what each one stops

| Layer | Stops | Does not stop |
|---|---|---|
| Tailnet membership (the owner's devices only) | Anyone not on the owner's tailnet | The owner's other devices; that is intended |
| Serve only, never Funnel; `doctor` checks `tailscale serve status --json` | Public internet exposure | — |
| Host binds `127.0.0.1` only and refuses any other address (G1) | LAN or Wi-Fi exposure | Local processes |
| `Host` must equal the configured `<desktop>.<tailnet>.ts.net`; a present `Origin` must be the same origin | DNS-rebinding pages in a desktop browser; cross-origin script | Native local clients that set the header |
| `Tailscale-User-Login` must equal `owner_login` (always required) | Users a node is shared with | Local processes, which can forge it |
| Per-device bearer token (§4.2), checked against the database on each request | Callers without a token; identifies the device for sessions and provenance | A local process that reads the token from the phone or the database (hashes only) |
| Allowlist with parameter constraints (§4.5); body, upload and admission limits (§4.6) | A buggy or compromised client reaching settings, keys, arbitrary files or unbounded work | Misuse of allowed methods within their constraints |

The identity check is always on, and tests inject the header with a fake.

### 4.2 Pairing

1. **Start on the desktop.** `learnloop-mobile pair --label "phone" --scope app|capture` creates a pairing record, which expires after 5 minutes. It prints two things:
   - **A QR code** for `https://<desktop>.<tailnet>.ts.net/pair#s=<secret>`. The secret is 256-bit and base64url-encoded. It sits in the URL **fragment**, so it never reaches the server's request line, access logs or `Referer`.
   - **A manual code** of 10 Crockford base32 characters (about 50 bits), for when scanning isn't possible.
2. **Open the pairing page.** `GET /pair` is a static page. It is identity-gated (§6.1), consumes nothing, and needs no bearer token. Its script reads the fragment, or asks for the manual code, and then posts.
3. **Exchange.** `POST /pair {secret | code, device_label}` requires the identity header. In **one transaction**, it checks the record (unexpired, unconsumed, and under its attempt limit), marks it consumed, creates the `mobile_devices` row, and stores the token **hash**. It then returns `{device_id, scope, token}` once.
   - Each pairing record allows 5 failed attempts.
   - Failed exchanges across all records are limited to 20 per 10 minutes. Beyond that, pairing is locked until the owner runs `pair` again.
4. **Store the token.**
   - The PWA keeps it in IndexedDB, so the service worker can read it for share-target uploads.
   - A capture-scope token can be copied from the pairing page into the iOS Shortcut's setup prompt. It is entered after installing the Shortcut and never embedded in a Shortcut file that might be shared.
5. **Lost response.** If the phone never receives the token, the owner pairs again. A device that has not been seen 24 hours after creation is revoked automatically, and `devices` lists it until then.
6. **Revoke.** `learnloop-mobile devices` lists devices with their scope and last-seen time. `learnloop-mobile revoke <id>` takes effect on the next request (no cache longer than 5 s). A lost phone is handled by revoking its token *and* removing the device from the tailnet. Revocation cannot erase data already cached on the phone (§4.4).

### 4.3 Token scopes

| Scope | Can reach | Issued to |
|---|---|---|
| `capture` | `POST /api/v1/capture`, `GET /api/v1/capture/{id}` | The iOS Shortcut (Android HTTP-client instructions exist in `docs/mobile-shortcuts.md`) |
| `app` | Everything in §6.1 that needs a token, including capture | The PWA |

A Shortcut token is a plaintext secret that is copied along with the Shortcut's data. That is why it gets the narrow scope.

**As built (M1):**
- **Wrong codes charge every active record.** The exchange has no pairing-record selector, so a wrong code counts against every active record's five-attempt limit. This can't evade the per-record cap.
- **The lock is durable.** The global 20-failures-per-10-minutes lock survives restarts, and only a local `pair` clears it.
- **Last-seen updates are throttled.** Device authentication and listing are read-only; admitted mutations update last-seen at most once a minute.

### 4.4 What leaves the machine, and what stays on the phone

**Over the tailnet to the phone (WireGuard-encrypted):** item prompts, feedback, tutor answers, the cached session, and the media of a photo or voice answer shown beside its grade. There is no bulk export to the phone.

**Stays on the phone after revocation:** the token until the client next gets a 401, the outbox (the learner's own unsent captures), and the cached session snapshot. On a 401 the PWA deletes the token and the session cache, keeps the outbox, and shows "scan a new token to send N captures". Outbox ids are globally unique, so sending them under a new token is safe (§7).

**To model providers, as on the desktop and accepted by the owner:**
- capture text;
- transcripts of photo and voice answers;
- the sanitized images and audio themselves when they are transcribed.

**Sanitization before anything is stored or sent (§6.7):**
- *Images:* the server decodes them with Pillow, which is already installed through manim and is now declared directly, with a decoded-size limit of 40 MP. It applies the EXIF orientation, re-encodes to JPEG or PNG with **all** metadata dropped (EXIF, XMP, ICC beyond sRGB, comments), and hashes the sanitized bytes server-side.
  - Accepted inputs: JPEG, PNG, WebP. HEIC is rejected with 415 unless D14 adds `pillow-heif`. The iOS Shortcut converts to JPEG before upload, and the PWA re-encodes through a canvas. Because the phone is an iPhone, rejecting HEIC depends on those two conversions never being skipped.
- *Audio (M3):* the server remuxes it with PyAV (already installed through manim; declared directly), drops container metadata, and enforces at most 10 minutes. Accepted inputs: M4A/AAC, MP3, WAV.

### 4.5 RPC allowlist

The allowlist is a frozen mapping in `learnloop_mobile/allowlist.py`. Each entry is `MobileMethod(name, milestone, kind: short|long, retry_safe, param_constraints)`. It names existing methods only, plus Slice 1's `diagnosis_status` once that exists.

| Milestone | Methods |
|---|---|
| M1 | none (the capture endpoints are not RPC) |
| M2 | `start_session`, `adopt_session` (new, PR-4), `get_session`, `end_session`, `update_session_checkpoint`, `clear_session_checkpoint`, `get_today_queue`, `open_queue_item`, `get_practice_item`, `get_probe_contract`, `save_practice_draft`, `submit_attempt`†, `submit_dont_know`†, `skip_practice_item`, `acknowledge_practice_submission`, `get_feedback`, `get_attempt`, `get_grading_clarification`, `answer_grading_clarification`†, and `diagnosis_status` once Slice 1 lands |
| M3 | `ask_tutor_question`†, `get_tutor_transcript`, `rate_tutor_answer`, `save_tutor_answer_note`‡, `promote_tutor_question`‡, `list_question_queue`, `resolve_question_event` |

† Long: accepted as a durable job (§6.3).
‡ Named exception to "no vault file operations". `save_tutor_answer_note` writes a note at a path the server chooses (`tutor_qa.py:231-249`). `promote_tutor_question` enqueues an authoring job that generates a proposal (`tutor_qa.py:252+`, `tutor/promotions.py:632`). Attaching to an existing topic may auto-apply **or route to review** (`promotions.py:640-654`). Both are allowed because both are the point of M3.

**Removed relative to revision 1:**
- `get_queue_revision` is replaced by the read-only `GET /api/v1/queue-revision`. The sidecar version can reload.
- `recover_practice_submission` is replaced by the job and submission status endpoints. The sidecar version can resume completions.

**Parameter constraints (enforced in the adapter, before dispatch):**
- `start_session`: `notes_md_path` is rejected. The phone sends `available_minutes`, plus `energy` and `sleep_quality` once Q14 decides the readiness form.
- `get_today_queue`, `skip_practice_item`, `open_queue_item`, `get_practice_item`: device eligibility comes from the request origin, never from a parameter (§6.4, §6.8).
- `submit_attempt`: `submission_id` must be present and non-blank. `self_grade` is rejected in M2, because the phone has no self-grading UI. `answer_md` must be absent when `answer_transcription_id` is present, or else equal the bound revision's text (§6.6).
- `ask_tutor_question` (M3): only the contexts the phone's screens originate (practice, feedback, standalone ask); `subject_id` must name an existing subject.
- `promote_tutor_question` (M3): `subject_id` and `learning_object_id` must exist; the intent comes from the handler's existing set.
- Any parameter naming a vault path, file or directory is rejected for every method.

**Never allowed.** Anything else in `METHOD_REGISTRY` returns 403 `method_not_allowed`. That includes:
- settings, AI providers and `sqlite_admin`;
- vault select, create and load;
- library file operations and graph editing;
- ingest administration, the registry and adjudication;
- `run_cli_command`;
- the probe-interaction methods `stop_probe_diagnosing`, `get_next_probe_item` and `start_overconfidence_probe` (M2).

A test enumerates the registry so this list cannot drift (G3). A method-name allowlist is not a capability audit, so each allowlisted method also gets a test showing that the constraints above hold.

### 4.6 Browser and HTTP hardening

- **Authentication order.** Host, then identity, then token are checked from the headers **before** any body is read. Expensive work is admitted only after that.
- **CORS and Origin.** The host never emits CORS headers. A request carrying an `Origin` that is not the host's own origin gets 403. Requests without `Origin` (the Shortcut) are accepted only with a valid token. API authentication is bearer-only; there are no cookies, so CSRF does not apply.
- **CSP on `/app/`:** `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'`. `style-src` allows inline styles because KaTeX needs them.
- **Caching.** API and RPC responses send `Cache-Control: no-store`. The service worker caches only the app shell and never `/api` or `/rpc`.
- **Limits:**
  - headers ≤ 16 KB;
  - JSON bodies ≤ 256 KB;
  - text capture ≤ 64 KB;
  - media ≤ `max_upload_mb` (default 20), counted while streaming whether or not `Content-Length` is sent;
  - 60 s body read deadline;
  - multipart: exactly one file part plus at most 10 fields;
  - responses 413, 415 and 503 (`host_busy`, retryable).
- **No per-token rate limits** (revision 3). Every client is the owner's, and admission below already bounds work.
- **Admission.** The RPC worker queue holds at most 16 requests and the job queue at most 8; beyond that the host returns 503 `host_busy`.
- **Static serving.** Only from the packaged app directory. No directory listing, no symlinks resolved outside it, and never a fallback to vault paths.
- **Logging.** `mobile_request_log` records the endpoint or method, status and duration, never payloads or tokens. Polling endpoints are not logged. Rows older than 90 days are pruned by the host.

### 4.7 `learnloop-mobile doctor`

Run by the owner; it reads local state only. It reports each check as **verified**, **failed** or **owner must confirm**:
- **Verified:**
  - the host is bound to loopback;
  - `tailscale serve status --json` shows 443 → `http://127.0.0.1:<port>`;
  - no Funnel is configured for that port;
  - the schema is at the expected version;
  - the configured vault exists;
  - the `mobile.env` mode is 0600;
  - grading readiness under the **unit's** environment: doctor reads `EnvironmentFile` and runs the same readiness check as `ready_grading_provider`.
- **Listed:** devices with their token label and last-seen time.
- **Not checked:** the tailnet policy. The tailnet is single-user and the phone has general access by design (D12).
- **Warned:** `tailscale status` health warnings, such as broken MagicDNS on the desktop. These do not stop the phone reaching the host, but they confuse debugging from the desktop.

---

## 5. Phone client options

| Option | Capture friction | Daily-loop UX | Build cost | Platform notes |
|---|---|---|---|---|
| **iOS Shortcut posting to `/api/v1/capture`** | Lowest: share sheet → "LearnLoop" → done | None | Very low: a Shortcut file plus docs | iOS: a Share Sheet Shortcut that runs "Convert Image" to JPEG, then "Get Contents of URL" (POST, bearer header from the setup prompt) |
| **PWA served by the host** | No share target on iOS (WebKit bug 194593 still open; listed unsupported). In-app capture box only | Good: installable, offline outbox, LaTeX input, camera and microphone through the browser | Moderate: the `apps/learnloop-mobile` screens | Service workers need HTTPS, which Serve provides. On iOS the outbox is durable only once the app is installed to the home screen, because Safari evicts storage of uninstalled sites after inactivity |
| Plain responsive web page | Same as the PWA, minus install and offline | Adequate | Low | No outbox when the desktop is unreachable |
| Tauri 2 mobile (native) | Native share extension | Best | High: signing, store or sideload builds, a second native target | Reconsider only if PWA limits bite: iOS share target, background capture, push |

**Recommendation.**
- **M1 ships the Shortcut only.** It works before any app exists, and it is the smallest thing that tests whether phone capture gets used.
- **M2 adds the PWA.** The Shortcut remains the share-sheet capture path, because iOS PWAs cannot be share targets.
- **Tauri mobile is deferred** (D4).
- **The phone is an iPhone** (D1, decided in revision 3).

---

## 6. Contracts

### 6.1 Endpoints and authentication

All are under `https://<desktop>.<tailnet>.ts.net`. **Identity** means the Host check plus `Tailscale-User-Login == owner_login`. **Token(s)** means identity plus a valid bearer token whose scope is `s` (§4.2–4.3); `app` tokens can reach everything a `capture` token can.

| Method and path | Auth | Milestone | Payload | Response | Idempotency |
|---|---|---|---|---|---|
| `GET /healthz` | none | M1 | — | `{ok: true}` (liveness only) | — |
| `GET /api/v1/status` | Token(capture) | M1 | — | `{vault_loaded, schema_ok, grading_ready, host_version}` | — |
| `GET /pair` | Identity | M1 | — | static pairing page | Consumes nothing |
| `POST /pair` | Identity | M1 | `{secret}` or `{code}`, plus `device_label` | `{device_id, scope, token}` (token shown once) | One-time record; atomic consume (§4.2) |
| `POST /api/v1/capture` | Token(capture) | M1 | JSON `{client_capture_id, kind: text\|url\|image, text?, url?, note?, source_app?, captured_at}`, or multipart with those fields plus one `file` (image) | First receipt `201 {capture_id, status:"received"}`; repeat `200` with the same body | `UNIQUE(client_capture_id)` (a ULID, globally unique). Same key with a different request fingerprint → `409 capture_conflict` |
| `GET /api/v1/capture/{capture_id}` | Token(capture) | M1 | — | `{status, routed_to?}` | — |
| `GET /app/*` | Identity | M2 | — | app shell, manifest, service worker (non-sensitive static assets) | — |
| `POST /rpc` | Token(app) | M2 | `{method, params, request_id?}` (§6.2) | `200 {ok, result}`, `202 {ok, accepted}`, or a typed error | Per method; long methods by `request_id` (§6.3) |
| `GET /api/v1/jobs/{job_id}` | Token(app) | M2 | — | `{state, result?, error?}` | — |
| `GET /api/v1/submissions/{submission_id}` | Token(app) | M2 | — | `{state: accepted\|running\|completed\|failed\|unknown, result?, error?}`; covers desktop submissions through `attempt_submission_receipts` | — |
| `GET /api/v1/queue-revision` | Token(app) | M2 | — | `{revision}` | — |
| `POST /api/v1/answer-media` | Token(app) | M2b | multipart `{session_id, practice_item_id, submission_id, modality: photo\|voice, file}` | `202 {transcription_id}` | `UNIQUE(submission_id, modality)` |
| `GET /api/v1/answer-media/{id}` | Token(app) | M2b | — | `{state, transcript_md?, revision?, error?}` | — |
| `GET /api/v1/answer-media/{id}/media` | Token(app) | M2b | — | the sanitized bytes | — |
| `POST /api/v1/answer-media/{id}/correct` | Token(app) | M2b | `{corrected_md, base_revision}` | `{revision, regrade_job_id}`; `409` if `base_revision` is stale | Compare-and-swap on revision. Allowed after grading; it triggers a regrade (§6.6 R1) |

The app shell and service worker are identity-gated but have no bearer token, because a first navigation cannot attach one. They contain no vault data. Every endpoint that reads or writes vault data needs a token.

### 6.2 The HTTP↔JSON-RPC adapter

`server._handle` (`server.py:48-103`) requires `"jsonrpc": "2.0"` and returns `None` when `id` is absent, so the host never forwards the phone's body as-is. The adapter:
1. **Validates the HTTP body.** It must be an object with exactly `method`, `params` (an object, default `{}`) and an optional `request_id`. Arrays (batches), extra keys and non-string methods get 400.
2. **Checks the allowlist** by exact name and milestone. A miss gets 403 `method_not_allowed`. It then applies the parameter constraints (§4.5): 422 `validation_error`.
3. **Sets the request origin** on the worker's context for this call only (§6.8).
4. **Builds** `{"jsonrpc":"2.0", "id": <host ULID>, "method", "params"}` and calls `_handle` on the RPC worker (short methods) or on the job worker through §6.3 (long methods).
5. **Translates the response:**
   - A result becomes `200 {"ok": true, "result": …}`.
   - A JSON-RPC error becomes `{"ok": false, "error": {code, message, retryable, details}}`, flattened from `error.data` (`errors.py:20-45`). That is the `CommandError` shape the desktop client already normalizes.
   - The HTTP status follows the stable code:

| Stable code | HTTP |
|---|---|
| `validation_error`, `invalid_request` | 422 |
| `not_found` | 404 |
| `method_not_allowed` | 403 |
| `session_open_elsewhere`, `session_moved`, `current_item_desktop_only`, `submission_conflict`, `capture_conflict`, `desktop_only` | 409 |
| `database_busy`, `completion_busy`, `host_busy` | 503 (retryable) |
| `grading_fallback_required` | 409 (retryable) |
| `internal` | 500 |

**Client retry policy.** The mobile client retries automatically only when `retryable` is true **and** the allowlist marks the method `retry_safe`. The `retry_safe` methods are:
- reads;
- `save_practice_draft`, `update_session_checkpoint` and `acknowledge_practice_submission`;
- every long method's acceptance, keyed by `request_id`.

`start_session`, `adopt_session`, `end_session`, `skip_practice_item` and M3 tutor writes are not retried automatically; the client shows the error and offers a manual retry. The compare-and-swap in §6.5 makes a manual retry safe.

### 6.3 Long mutations: accepted jobs

**Why.** `submit_attempt` grades synchronously (`practice.py:489-611`), with a provider timeout of 180 s by default (configurable). A phone on a flaky link, or one that backgrounds the browser, will drop long requests. The sidecar's `recover_practice_submission` returns `pending` whenever no attempt or receipt exists. That status cannot distinguish queued, grading, failed before commit, never received, and lost in a restart, so the phone could poll forever.

**Contract.**
- **Acceptance.**
  - A long method needs a `request_id`. For submits, `request_id` is `submission_id`, which is required.
  - The host canonicalizes `params` (sorted-key JSON after constraint checks), hashes it, and in one transaction inserts a `mobile_jobs` row in state `accepted`, or finds the existing one.
    - **Same id and same hash:** return the existing job's current state. Identical retries are coalesced, with no second provider call from the host.
    - **Same id and a different hash:** `409 submission_conflict`.
  - For photo and voice answers, the same transaction marks the bound transcription consumed (§6.6).
  - The host returns the job only after this commit.
- **Execution.** The job worker owns a copy of the accepted params and runs the handler through `_handle` to completion, whether or not the HTTP client is still connected.
  - States: `accepted → running → completed | failed`.
  - On `completed`, `result_json` is the handler's return value. For submits that is the same payload stored as the submission receipt.
  - On `failed`, the job stores the typed error (`grading_fallback_required`, `validation_error`, `item_retired`, `host_restart_exhausted`, `internal`, …).
  - The host then bumps `queue_revision` (PR-7).
- **Response.** `/rpc` waits up to 15 s on the job. It then returns either the final `200` or `error`, or `202 {ok: true, accepted: {job_id, request_id, state}}`.
- **Polling.** The PWA polls `GET /api/v1/jobs/{job_id}` every 2 s, on the read-only path, until a terminal state. It then calls `acknowledge_practice_submission`, as the desktop does.
- **Restart recovery.** Each row records the `host_boot_id` that ran it. On start, the host re-examines rows in `accepted` or `running` from another boot:
  - **A receipt exists:** mark `completed` with the receipt as the result.
  - **The attempt committed without a receipt:** requeue. The handler's `_cached_submission` resumes the saved completion; it does not re-grade.
  - **No attempt:** requeue, which grades again; no evidence was written.
  - After 3 boots the job becomes `failed` with `host_restart_exhausted`, and the draft remains in the checkpoint.
- **Phone without self-grade.** When grading is unavailable, the job fails with `grading_fallback_required`. The phone shows "AI grading is unavailable; your answer is saved — retry later or finish on the desktop". The draft stays in the checkpoint.

`answer_grading_clarification` (a regrade) and the M3 `ask_tutor_question` follow the same contract with a client-minted `request_id`. Desktop calls are unchanged and stay synchronous.

This is the same shape as Slice 1's `diagnosis_status` polling. Nothing changes in grading itself. Making the grader faster is Q16, not this spec.

### 6.4 Device eligibility

**Module.** `learnloop/scheduling/device_eligibility.py` (PR-6) exposes `ineligibility_reason(vault, item, device_class) -> str | None`. For `phone`, it returns a reason for:
- error-hunt items;
- laddered stems;
- multi-turn teach-back (until voice teach-back);
- a prompt or stem that embeds an image, links `llpdf://`, or references an item asset;
- practice modes on `DESKTOP_ONLY_MODES`.

Text cues such as "see the figure below" are logged as `suspected_figure` in the M2 report. They are not filtered until reviewed, because pattern lists misfire.

**Where it applies.** The class comes from the request origin (§6.8), never from a parameter, and is applied everywhere an item can reach the phone:
- `get_today_queue` filters before `finalize_scheduler_offer`, so the offer receipt matches what the phone showed. It adds `device_deferred_count` to the response; the field is absent for the desktop.
- `skip_practice_item` rebuilds the slate with the same filter. Note what skip actually does: it writes **no attempt evidence**, but it publishes a new offer receipt and clears the session checkpoint (`practice.py:790-818`).
- `open_queue_item` and `get_practice_item` refuse an ineligible item with `desktop_only`.
- `adopt_session` handles the case where the current item is ineligible (§6.5).

**Diagnostic probes in M2.**
- The desktop calls `get_probe_contract` for every item it serves. Committing the presentation *is* the serve event (`PracticeScreen.tsx:414-417`), so the phone does the same.
- When the contract is inactive, the item is ordinary practice.
- When it is active, the phone does not render it. It shows "This is a diagnostic check — continue it on the desktop" and moves to the next queue item without calling skip.
- **Implementation check before M2:** confirm that a committed, unanswered probe presentation resumes correctly on the desktop, as it does after the app closes mid-item. If it does not, `ineligibility_reason` must exclude probe-capable items at queue time instead.

**Mixed devices** (D6): ineligible items are filtered, and the phone shows "N items waiting for the desktop".

**Desktop requests** take the `desktop` class and stay byte-identical to today (G9).

### 6.5 Sessions across devices

**The rule stays: one open session.** Two concurrent sessions would break session-scoped caps. Those caps are counted per session id, and their defaults (4 probe observations per session, 1 follow-up per topic per session) are configurable.

**What's wrong today.** `start_session` creates the new session, then ends the others, in two separate commits (`sessions.py:41-47`; `repositories.py:9037-9049`). Two processes can interleave so that both sessions are ended. An ended session raises a generic `validation_error` (`sessions.py:135-141`), so the desktop cannot tell it was taken over.

**PR-4. New repository operations, each one `BEGIN IMMEDIATE` transaction, shared by the desktop sidecar and the host:**
- **`sessions` gains columns.** `owner_device_id TEXT` (null means the desktop) and `owner_generation INTEGER NOT NULL DEFAULT 0`.
- **`start_session_exclusive(fields, owner_device_id, replace: str | None)`** reads the open session.
  - **None open,** or the open session already belongs to this caller's device: proceed as today, silently replacing the caller's own session.
  - **Another device owns it and `replace` is null:** return `session_open_elsewhere` with that session's snapshot (owner label, current item, whether a draft exists, and the draft's first line).
  - **`replace` equals that open session's id** (the learner chose "start fresh"): copy its checkpoint into `session_handoffs`, end it, and create the new one. This is a compare-and-swap; a stale `replace` returns `session_open_elsewhere` again.
- **`adopt_session(session_id, owner_device_id, expected_generation)`** is a compare-and-swap on `owner_generation`. It sets the owner, increments the generation, and records the handoff in `session_handoffs`. The checkpoint is untouched. The session id, and therefore the caps, the stable `submission_id` and the scheduler-offer binding, carry over.
  - If the checkpoint's current item is ineligible for the adopting device **and** has a non-empty draft, it returns `current_item_desktop_only`. The learner then finishes it on the desktop or starts fresh, which preserves the draft in `session_handoffs`. Adopting never silently loses a draft.
- **Ownership on writes.** Every session-scoped write checks `owner_device_id` against the request origin (§6.8). That covers `update_session_checkpoint`, `clear_session_checkpoint`, `save_practice_draft`, `skip_practice_item`, `submit_*` acceptance, `acknowledge_practice_submission` and `end_session`. A mismatch returns `session_moved` (not retryable), with the owner label and generation. Reads are unrestricted.
  - A job accepted before a handoff completes normally, because ownership was checked at acceptance.
- **`patch_checkpoint`** (`sessions.py:108-132`) runs its read-merge-write inside `repository.atomic()`.

**Adopting a checkpoint that carries a `submission_id`.** The adopting client first calls `GET /api/v1/submissions/{id}`.
- **Completed:** it shows that feedback.
- **Accepted or running:** it polls.
- **Unknown:** it treats the checkpoint as a draft. If the desktop was in fact mid-grade, a phone resubmit with the same id hits the unique index, and the host returns the winner's receipt, at the cost of a duplicate provider call.

**Desktop changes (M2; the desktop is not unchanged):**
- handle `session_open_elsewhere` with an adopt / start fresh / cancel prompt;
- handle `session_moved` with a banner ("This session continued on your phone"), stop writing, and offer to adopt it back;
- start sessions through `start_session_exclusive`;
- PR-7's app-level revision poll.

**Two devices at once.** Writes from the non-owner are rejected, so simultaneous use is no longer last-writer-wins (D5).

**The readiness form on the phone** depends on Q14. Until it's answered, the phone sends `available_minutes` only.

### 6.6 Answering on a phone: typed, photo, or voice

| Modality | Milestone | Path | Notes |
|---|---|---|---|
| Typed | M2a | LaTeX/Markdown editor → `answer_md` | Unchanged contract |
| Photo of a handwritten answer | M2b | `answer-media` → transcription job → `submit_attempt(answer_transcription_id, revision = latest)`, normally the raw transcript → the grade is shown **beside the rendered transcript and the image** → optional **"Fix what was read"** (compare-and-swap) → new revision → regrade, which supersedes and keeps the earlier grade | Transcribed on the `image_transcription` route from `spec_image_dropin_ingest.md` §3. M2b waits for that route, or this spec adds it, with the same contract |
| Voice | M3 | `answer-media` → `ingest/transcription.py:67` `transcribe_audio`, which is synchronous and returns cues; the job worker runs it, and the cue text joined in order becomes `transcript_md` → submit → grade shown with the transcript → optional fix and regrade | Best for explanations and "why" answers; poor for symbol-heavy math |

**Rules:**
- **R1. Bind and freeze.**
  - A submit carrying `answer_transcription_id` is bound to that transcription's **latest revision** at submit time (normally revision 0, the raw transcript). The host checks that:
    - the transcription is in state `transcribed` or `corrected`;
    - the bound revision is its latest revision;
    - its `session_id`, `practice_item_id`, `submission_id` and device match the submit.
  - The host then **sets `answer_md` from that revision's text itself**. A client `answer_md` must be absent or byte-identical; otherwise the submit gets `409 submission_conflict`.
  - Job acceptance and `state = consumed` (with `consumed_by_submission_id`) commit in **one transaction**.
  - **A correction after grading** (`POST …/correct`) creates a new revision, and the host requests a regrade of the attempt with `answer_md` set from it. The regrade is a new grading epoch that supersedes the old one and keeps it, using the existing regrade path. A revision once graded is never edited.
  - Corrections made after the feedback was shown are recorded as `corrected_after_feedback` (§10), so their effect on grades stays visible.
- **R2. Grading input is unchanged.** Whichever grader is live receives the bound revision's text exactly as it would receive typed text. With Slice 1, that is `BlindGradingContext`. The transcript is the current answer, not learner history. Whether the grader also receives the image is **D7**; the recommendation is text only.
- **R3. Recording** (§8):
  - `answer_transcriptions` (RAW_LEDGER, immutable) holds the media hash, the model, the raw transcript and the transcription time.
  - `answer_transcript_revisions` (RAW_LEDGER, append-only) holds one row per correction revision, with its text, its time, and whether it followed the feedback.
  - `answer_transcription_jobs` (WORKFLOW) holds the lifecycle: `pending | transcribed | failed | consumed | corrected`, the error code, the latest revision and `consumed_by_submission_id`.
  - The edit distance is computed at consumption.
  - The modality of an attempt is derived by joining `attempts.submission_id` to `consumed_by_submission_id`, and is typed when there is no match (§6.8).
  - `latency_seconds` is client-reported, as today, measured from item display to the photo or recording.
- **R4. Contesting.** The media stays attached to the attempt through that join. The desktop's feedback and contest view gains an attachment panel, served from the originals store by hash. A misread the learner missed can therefore still be fixed through the existing regrade path.
- **R5. No penalty for corrections.** Fixing a misread is the point. Correction rates, and the share made after feedback, are reported (§10) so that corrections used to improve answers after seeing the feedback stay visible.

`SubmitAttemptInput` (`practice.py:94-114`) gains no new fields. `answer_transcription_id` is an adapter-level parameter that the host resolves to the latest revision before dispatch. Desktop calls are unchanged.

### 6.7 The capture inbox: M1 storage now, background processing in M3

**M1 (stores and lists; processing comes in M3 under the daily-loop defaults, T6).**
- **Receipt order.**
  1. Authenticate the request.
  2. Stream the body under its limits.
  3. Fingerprint the request (sha256 of the canonical fields plus the raw media bytes).
  4. Sanitize the media (§4.4) and store it with `learnloop.ingest.originals.store_original_bytes` (`ingest/originals.py:29`), under the server-computed hash of the sanitized bytes.
  5. In **one transaction**, insert `capture_inbox` and `capture_routes(state=new)`.
  6. Respond only after the commit.

  A failure after step 4 leaves an unreferenced, content-addressed media file, which is harmless; `doctor` reports such files. `vault/paths.py:90` only computes the originals path; the store is `ingest/originals.py`.
- **URLs** must be `http(s)` URLs or arXiv ids. Anything else, including `file:` and bare paths, is rejected with 422, because the desktop's source field also accepts local paths.
- **The desktop lists the inbox** in a new Inbox strip on Today and in `learnloop inbox list`. The strip polls the new sidecar method `get_inbox_summary` every 30 s while Today is mounted, and when the window regains focus. Each entry has one-click routes into **existing** paths:

| Capture | Route | Existing path, and what it needs |
|---|---|---|
| Text | "Make a card" | `WriteCardDialog` gains `initialPrompt` and `captureId` props; today it takes only default learning-object fields, and prompt and answer start empty (`WriteCardDialog.tsx:18-32`) |
| URL or arXiv id | "Quick Add source" | `QuickAddDialog` already supports source prefill (`QuickAddDialog.tsx:33`); it gains `captureId` |
| Text question | "Ask tutor", then promote | `ask_tutor_question` → `promote_tutor_question`. Attaching to an existing topic may auto-apply or route to review, and minting a new topic goes to review (`tutor/promotions.py:640-654`) |
| Photo | "Photo → item" | the image drop-in pipeline, when built; until then "Make a card" with the capture recorded as provenance |
| Any | "Dismiss" | new sidecar method `dismiss_capture` |
| Any | "Purge" | new sidecar method `purge_capture`, for accidental sensitive shares: nulls the text, URL and note, deletes the media file, and sets `purged_at` |

- **Routing is recorded by the backend call that succeeded, not by the dialog that opened.** The card-authoring, Quick Add and tutor-ask methods each gain an optional `capture_id`. When it is present, the method records `capture_routes(state=routed, route, result_refs_json)` idempotently after its own commit. A cancelled or failed dialog leaves the capture `new`.
- **New sidecar methods** (`get_inbox_summary`, `list_capture_inbox`, `dismiss_capture`, `purge_capture`) are desktop-only. They are default-denied on the phone (T3).

**After the owner answers the daily-loop questions,** a background processor replaces the manual routes:
- **Q1:** inbox-first, straight-to-items, or hybrid.
- **Q2:** inferred topic.
- **Q3:** an LLM-solved and verified answer key, reusing the verified-reference contract in `spec_embedding_consumers_v1.md` §5.3.
- **Q6:** inferred intent.

It runs as a leased job, and the phone's `GET /capture/{id}` shows its result. That processor is specified in the daily-loop spec, not here.

### 6.8 Request origin and provenance (PR-5)

**Origin on the context.** `SidecarContext` gains `request_origin: RequestOrigin | None`, holding `device_id` and `surface`. The host sets it around each call; the desktop sidecar leaves it `None`, which means the desktop. Handlers read it; parameters never carry it.

**Where it is recorded.**
- **Attempts:** `entry_surface` is hard-coded to `"desktop_practice"` today (`practice.py:528`, `:638`). Handlers take it from the origin: `phone_practice` for host calls, unchanged for the desktop. `entry_surface` is already a cohort key in `substrate/data_quality.py:78`, so the device split in §10 comes from existing reports.
- **Offers and submission bindings:** `finalize_scheduler_offer` and `bind_submission_offer` default to `desktop_queue` and `desktop_practice` (`db/stores/collection.py:42`, `:77`). Handlers pass `phone_queue` and `phone_practice` from the origin.
- **Session ownership** uses `device_id` (§6.5).
- **Modality** comes from the transcription binding (§6.6).
- **No attribution from the session's owner.** `owner_device_id` changes on handoff, so an attempt's device is never inferred from it.

---

## 7. Offline behaviour

**Capture never fails silently.**
- **PWA:** an IndexedDB outbox. Each record holds a manifest keyed by `client_capture_id` (a ULID) and the media as a `Blob`.
  - It is flushed on app open, when the app regains focus, and every 60 s while open. iOS Safari has no Background Sync, so flushing happens only while the app is open. On iOS the outbox is durable only for the home-screen-installed app.
  - A record is removed only on 201 or 200.
  - Responses are classified:

| Response | Outbox action |
|---|---|
| Network error, timeout, 5xx, 503, 429 | Retry with backoff |
| 401 | Stop flushing; show "scan a new token to send N captures" |
| 403 | Stop flushing; show the reason |
| 409 `capture_conflict` | Keep the record and flag it for the learner |
| 413, 415, 422 | Mark it permanently failed, show the reason, and keep it until dismissed |

  - Quota errors are surfaced, not swallowed.
- **iOS Shortcut:** on a non-2xx response or a timeout, it saves `Files/LearnLoop/outbox/<client_capture_id>.json` (the manifest) and, for images, `<client_capture_id>.jpg` beside it, and says so.
  - A second Shortcut, "Flush LearnLoop outbox", re-posts each pair and deletes both files only on 2xx.
  - On 409 it moves them to `outbox/conflict/`. On 401 it stops and says to paste a new token.
- **A new token** issues a new `device_id`, but captures are unique by `client_capture_id` alone, so a capture already received under the old device is not duplicated.

**Practice requires the desktop online** (D9, recommended). Offline practice would mean either delayed grading, so feedback arrives hours later and loses much of its value for learning, or self-grading, which carries lower authority. Neither is worth building before usage data exists. When the desktop is unreachable, the PWA shows "desktop offline", the capture box, and the outbox count.

**A sleeping desktop is the main availability risk** (D11). The options are:
- accept it;
- have the host hold a sleep inhibitor while a session is open;
- use Wake-on-LAN through an always-on tailnet node;
- later, move the host and vault to an always-on machine.

---

## 8. Persistence

**Migration numbers.** The baseline head on 2026-10-11 is `migrations/165_model_call_budgets.sql`, with `fixtures/migration_head_165/`. `spec_blind_grading_diagnosis_split_v1.md` already proposes 166. Numbers are assigned when each migration lands (`ls migrations/`), following `CLAUDE.md`:
- classify every table in `db/table_roles.py`;
- upgrade and rename the head fixture, keeping it in rollback mode;
- update its README and the hard-coded paths;
- rerun `db_generate_reference.py` and `db_validate_reference.py`.

M1's tables land in one migration; M2's in a second; M2b's and M3's in their own.

| Table | Role | Milestone | Contents |
|---|---|---|---|
| `mobile_devices` | WORKFLOW | M1 | `id`, `label`, `token_hash`, `created_at`, `last_seen_at`, `revoked_at` |
| `capture_inbox` | RAW_LEDGER | M1 | `id`, `client_capture_id` (UNIQUE), `device_id`, `kind`, `text`, `url`, `note`, `media_sha256`, `media_mime`, `source_app`, `request_sha256`, `captured_at` (client), `received_at`, `purged_at`. Immutable except purge (§6.7) |
| `capture_routes` | WORKFLOW | M1 | `capture_id`, `state` (`new`\|`routed`\|`dismissed`\|`processing`\|`failed`), `route`, `result_refs_json`, lease fields for the later processor |
| `mobile_request_log` | WORKFLOW | M1 | `device_id`, `endpoint` or `method`, `status`, `duration_ms`, `at`; no payloads; polling not logged; 90-day pruning |
| `mobile_jobs` | WORKFLOW | M2 | `id`, `device_id`, `request_id` (UNIQUE with `device_id`), `method`, `params_json`, `params_sha256`, `state` (`accepted`\|`running`\|`completed`\|`failed`), `result_json`, `error_json`, `host_boot_id`, `boot_attempts`, `accepted_at`, `started_at`, `finished_at` |
| `session_handoffs` | RECEIPT | M2 | `id`, `session_id`, `kind` (`adopt`\|`replace`), `from_device_id`, `to_device_id`, `generation`, `checkpoint_json`, `at` |
| `sessions` | (existing) | M2 | `ADD COLUMN owner_device_id TEXT` (null = desktop), `ADD COLUMN owner_generation INTEGER NOT NULL DEFAULT 0` |
| `answer_transcriptions` | RAW_LEDGER | M2b | `id`, `modality`, `media_sha256`, `media_mime`, `model`, `raw_md`, `captured_at`, `transcribed_at` |
| `answer_transcript_revisions` | RAW_LEDGER | M2b | `transcription_id`, `revision`, `text_md`, `created_at`, `corrected_after_feedback`, `regrade_epoch_id` |
| `answer_transcription_jobs` | WORKFLOW | M2b | `transcription_id`, `device_id`, `session_id`, `practice_item_id`, `submission_id` (UNIQUE with `modality`), `state`, `error_code`, `latest_revision`, `consumed_by_submission_id`, `edit_distance`, `consumed_at` |

**No change to attempts.** The surface goes in the existing `entry_surface`; modality comes from the join (§6.8).

**Host configuration** lives in `$LEARNLOOP_CONFIG_DIR/mobile.toml`, not in a vault's `learnloop.toml`, because it describes the machine. It is a typed Pydantic model in `learnloop_mobile/config.py`:
- `enabled = false` (the host refuses to start otherwise);
- `vault` (absolute path);
- `hostname` (`<desktop>.<tailnet>.ts.net`);
- `port = 8765`;
- `owner_login`;
- `max_upload_mb = 20`.

Provider keys for the unit go in `mobile.env` (§3.1).

**Host vault vs desktop vault** (D15). The host serves one pinned vault. When the desktop has a different vault open, its Inbox strip shows "Phone host serves <vault>". The desktop never switches the host.

**Replay.** The new RAW_LEDGER rows carry no evidence semantics. Replay ignores them, apart from attempts' existing replay, so rebuild equivalence is unaffected.

---

## 9. Rollout

| Milestone | Build | Owner does | Gate to proceed |
|---|---|---|---|
| **M1 — Capture** | `learnloop_mobile` package and script; `mobile` extra (Starlette, uvicorn, `python-multipart`); import-linter entry; capture host (no `SidecarContext`; §3.1); pairing with `capture` / `app` scopes (§4.2–4.3); `/healthz`, `/api/v1/status`, capture endpoints; `learnloop.capture` (sanitization, inbox, routes); M1 migration; desktop Inbox strip with the routing additions in §6.7; `learnloop inbox list`; native iOS Shortcuts (capture, photo, flush; JPEG conversion; save-before-send outbox in iCloud Drive); `doctor`; systemd unit and `mobile.env` | Pairs the Shortcut (capture scope) and pastes the token into its setup question; captures from the share sheet for ~2 weeks; routes from the desktop | G1–G5, G6a, and acceptance checks A1–A3 pass. Report: captures per week, share routed vs dismissed, time to route, outbox flushes, failures. If captures are rare, stop and ask why before M2 **Status (2026-10-12):** built on `mobile/m1`; 6,268 tests and 66 durability tests pass; A1–A3 pending on the phone |
| **M2 prerequisites** | PR-1 through PR-7 (§3.3), each landed and tested on its own; the probe-presentation check in §6.4 | — | Their tests pass; the full suite and the durability lane are green |
| **M2a — Typed practice on the phone** | `apps/learnloop-mobile` PWA (Capture, Today, Question, Feedback); `/rpc` adapter with the M2 allowlist; RPC and job workers in secondary attach; accepted jobs and status endpoints; session handoff; device eligibility; origin provenance | Short phone sessions alongside desktop use | G1–G12 and A4 pass. Report: phone sessions and items per week, completion, submit-to-feedback p50/p95, share of submits returning 202, contest rate on phone vs desktop attempts |
| **M2b — Photo answers** | `answer-media` endpoints, transcription jobs, immediate grading on the transcript, the post-grade "Fix what was read" screen with regrade, binding (§6.6), desktop attachment panel; requires the `image_transcription` route | Photo answers for handwritten work | G8 passes. Report: transcription correction rate (and share after feedback), submit-to-grade time, contest rate on photo attempts |
| **M3 — Tutor and voice** | M3 allowlist; tutor asks as jobs; promotion runner in the host (§3.1); voice answers; the background capture processor under the daily-loop defaults (save means reference; silent filing and verified solving; one-tap "Practice this") | Asks the tutor from the phone; promotes questions | Report: tutor questions per week, share promoted, promoted items later answered |
| Later | Offline self-check pack (self-graded, flagged); voice teach-back; a real math keyboard; Tauri mobile if PWA limits bite; the reader (separate spec) | — | Each on its own report |

---

### 9.1 As built (M1, 2026-10-12)

The full record is `docs/reviews/mobile-m1.md` on `mobile/m1`.
- **Native-only Shortcuts.** There is no Scriptable or companion app.
  - Native HTTP actions can't reliably classify status codes, so 401 and 409 become visible fail-stop retention plus manual recovery, not automatic re-pairing or quarantine.
  - Files are saved to the outbox (`iCloud Drive/Shortcuts/LearnLoop/outbox`) before sending, and deleted only after a parsed receipt. The outbox is not tailnet-local.
  - The Shortcut assets are unsigned plist workflows. Signing and import are checked in A3.
- **Publication and purge share a short SQLite writer reservation.** Image decoding happens before the transaction, and storing sanitized bytes happens inside it, which avoids a purge race. Only file publication, fsync and SQL hold the lock.
- **Purge leaves things that are shared.** It keeps originals shared with other captures or sources, and destinations already created. It removes capture text and route payloads, and leaves a fingerprint tombstone. Failed unlinks stay as deletion-pending entries, with a retry.
- **Routing to the tutor** creates a deterministic reference-note anchor in the chosen subject. A committed but incomplete tutor event is not reissued automatically, which avoids duplicate spend.
- **`/api/v1/status` reports `grading_ready = false`,** because M1 has no grading runtime. `doctor` checks grading readiness separately, against the unit's EnvironmentFile.
- **Only admitted mutations are written to `mobile_request_log`.** Rejected or rate-limited traffic is not, and pruning runs on admitted work, never at startup.
- **A schema-set mismatch makes the host exit with code 78.** It runs no sidecar, vault loader, ingest runner, migrations or startup maintenance.
- **Dependencies.** The `mobile` extra pins Starlette, uvicorn and `python-multipart`. Pillow is a direct dependency, used to decode, orient and strip metadata.
- **Tailnet policy.** `doctor` prints a revision-2 phone-only grant example. Under D12, applying it is optional. Revision 3's acceptance A2 (Serve mapping only, no off-tailnet reachability) is the check that matters.
- **Integration.** The branch is based on `1a0f7a0` and claims migration 167. It takes the next free number when it merges, after the Slice A Phase 2/3 integration.

## 10. Evaluation

**Correctness gates (pass/fail):**

| Id | Gate |
|---|---|
| G1 | The host refuses to start unless its bind address is loopback, and refuses (status 78) on a schema mismatch. `doctor` fails on any non-serve or Funnel exposure of the port |
| G2 | Endpoint matrix (§6.1). No token → 401. Revoked token → 401 within 5 s. Wrong or missing `Tailscale-User-Login` → 403. Wrong `Host` or a foreign `Origin` → 403. Identity headers sent to the loopback port without a token → 401. `/app/*` contains no vault data |
| G3 | Every `METHOD_REGISTRY` method outside the allowlist returns 403, checked by enumerating the registry; new methods are denied by default. Batches, extra envelope keys and non-object params → 400. Each parameter constraint in §4.5 is enforced |
| G4 | Capture: the same `client_capture_id` twice gives one row, 201 then 200 with the same body. The same id with a different payload → 409. The inbox row and initial route commit atomically. Stored media are re-encoded with no EXIF, XMP or GPS, orientation is preserved, and the hash is computed server-side. HEIC → 415 (unless D14). Body, upload and rate limits return 413 or 429 |
| G5 | Pairing: single use; the 5-per-record and 20-per-10-minute limits (durable lock); consume and token creation are atomic; the fragment secret never appears in request logs; unclaimed devices expire; `revoke` takes effect within 5 s |
| G6a | Host coexistence (M1, durability lane): starting and stopping the host performs no migration, maintenance, projection refresh, cold-probe scheduling, lease recovery or synthesis sweep. That includes a desktop synchronous synthesis run older than the lease cutoff, which survives a host start. Capture writes interleaved with desktop writes lose nothing; contention surfaces as the retryable `database_busy` |
| G6b | Two-process practice (M2, durability lane): the desktop sidecar and the host submit, read and sync concurrently with no lost writes. A content sync interleaved with an attempt keeps the attempt's scheduling fields (PR-2). Leased jobs never run twice. The two in-host workers behave as two processes |
| G7 | Jobs: a dropped connection mid-submit yields exactly one attempt and a `completed` job with the receipt. A host restart while running yields `completed` or a typed `failed`, never indefinite `accepted` or `running`. The same `request_id` with different params → 409. Identical retries make one provider call from the host |
| G8 | Transcript binding: every grading epoch names the revision it graded, and its text equals that revision's. A correction creates a new revision and a superseding regrade epoch; the earlier grade is kept. A submit naming a mismatched or superseded transcription is rejected |
| G9 | Device eligibility applies in `get_today_queue` (before `finalize_scheduler_offer`), the skip rebuild, `open_queue_item`, `get_practice_item` and adoption. An active probe contract is not rendered on the phone. Desktop responses are byte-identical to today |
| G10 | Sessions: interleaved starts from two processes leave exactly one open session. A stale `replace` or a stale `expected_generation` is rejected. Writes from the non-owner → `session_moved`. Adopting carries the checkpoint, submission id and caps. Starting fresh preserves the replaced draft in `session_handoffs`. Concurrent admission at the probe-observation cap boundary never exceeds the cap |
| G11 | Provenance: phone attempts carry `entry_surface = phone_practice` and phone offers `phone_queue`. Desktop values are unchanged. No parameter can set either |
| G12 | Freshness: a YAML change made by the desktop is visible to the host's next request after at most 2 s. A committed phone mutation bumps `queue_revision`, and the desktop's app-level poll refetches. A desktop whose session was adopted shows `session_moved` without a restart |

**Acceptance checks on real devices (manual, recorded in the milestone report):**
- **A1.** `tailscale serve` strips a client-sent `Tailscale-User-Login`, and the host sees the real login.
- **A2.** `tailscale serve status --json` shows only the expected 443 → loopback mapping, and the URL does not resolve or connect from a device off the tailnet.
- **A3.** The iOS Shortcut captures with Tailscale disconnected beforehand (VPN On Demand), and its outbox flushes after the desktop wakes.
- **A4.** The PWA installs to the home screen. A capture made in the PWA while the desktop sleeps arrives later. A submit backgrounded mid-grade shows feedback on return.

**Usage signals** (report-only, monthly; no thresholds): those listed per milestone in §9, plus:
- the device split of attempts, by `entry_surface` cohort;
- whether phone use adds sessions rather than moving them from the desktop.

That last question is the one that matters for the daily loop.

---

## 11. Tests

- `test_mobile_host_auth.py`: bind refusal; schema-mismatch exit; the endpoint matrix; token issue, hash and revoke; Host and Origin checks. (G1, G2)
- `test_mobile_pairing.py`: single use, attempt limits, durable lock, atomic consume, log redaction, unclaimed-device expiry. (G5)
- As built, also: `test_mobile_allowlist.py`, `test_mobile_capture.py`, `test_mobile_doctor.py`, `test_mobile_host_coexistence.py`, `test_mobile_shortcuts.py`, `test_capture_domain.py`, `test_capture_desktop.py`, `test_capture_originals_race.py`, `test_capture_route_recovery.py`.
- `test_mobile_allowlist.py`: registry enumeration; envelope rejection; per-method parameter constraints; allowed methods pass through `_handle`, with errors translated as in §6.2. (G3)
- `test_mobile_capture.py`: JSON and multipart capture; the body-limit middleware (oversized bodies rejected before parsing, with and without `Content-Length`); repeat and conflict; atomic commit; the sanitization corpus (JPEG with GPS EXIF, rotated, PNG with text chunks, WebP, HEIC rejected); size and rate limits; URL validation; routing through each backend `capture_id` path; dismiss and purge. (G4)
- `test_mobile_host_coexistence.py` (durability lane): host start and stop beside a seeded live synchronous synthesis run and live leases; capture writes interleaved with desktop writes. (G6a)
- `test_secondary_attach.py`: `load_secondary` performs no writes (checked by comparing the database before and after); content-fingerprint reload. (PR-1, G12)
- `test_state_sync_scheduling_race.py`: an attempt committed between snapshot and update keeps its scheduling fields. (PR-2, G6b)
- `test_mobile_two_process.py` (durability lane): two real processes on one fresh vault interleaving submits, reads, syncs and a leased job. (G6b)
- `test_mobile_jobs.py`: a client disconnect during a fake slow grade; a host restart in `accepted`, in `running` with no attempt, and in `running` with an attempt but no receipt; coalescing; conflicts; `grading_fallback_required`. (G7)
- `test_answer_transcription.py`: immediate grading on revision 0; the correction compare-and-swap; a correction triggers a superseding regrade that keeps the old grade; graded text equals the bound revision; the `corrected_after_feedback` flag; the modality join. (G8)
- `test_device_eligibility.py`: each ineligibility reason; every application site; probe contract handling; the desktop byte-identical. (G9)
- `test_session_ownership.py`: interleaved exclusive starts; replace and adopt compare-and-swap; `session_moved` on every session-scoped write; draft preservation; the cap boundary under concurrency. (G10)
- `test_request_origin.py`: `entry_surface` and offer surfaces from the origin; parameters cannot set them. (G11)
- Mobile app (vitest): the HTTP `call()` maps commands to `/rpc` and errors to `CommandError`; `202` handling; the retry policy; outbox persistence, response classification and flush; token pickup from the URL fragment; a photo or voice answer submits without a confirm step and shows its transcript beside the grade.
- Fakes: a fake identity-header injector and a fake transcription provider. No automated test calls Tailscale; A1–A4 cover the real deployment.

---

## 12. Open decisions

| # | Decision | Recommendation |
|---|---|---|
| D1 | Phone platform: iOS, Android, or both? | **Decided (owner, 2026-10-11): iOS.** The phone is `iphone-13-pro-max` on the owner's tailnet |
| D2 | Host: a separate `learnloop-mobile serve` user service, or embedded in the desktop sidecar? | Separate. The phone must work with the desktop app closed, and the sidecar is a single-threaded stdio loop |
| D3 | HTTP stack: standard library, or Starlette, uvicorn and `python-multipart`? | **Decided (owner, 2026-10-11): Starlette + uvicorn + `python-multipart`** as a `mobile` extra (§3.1). The §4.6 limits are still implemented explicitly as middleware |
| D4 | Client: a separate small mobile app reusing DTOs and render components, responsive desktop screens, or Tauri mobile? | A separate PWA (`apps/learnloop-mobile`). Tauri mobile only if PWA limits bite |
| D5 | Sessions: one shared session with handoff, or concurrent per-device sessions? | One shared session with atomic handoff and ownership (§6.5). Per-device sessions break session-scoped caps |
| D6 | Phone-ineligible items: filter them from the phone queue, or show them with "best on desktop"? | Filter before offer logging, and show a count ("3 items waiting for the desktop") |
| D7 | Photo answers: does the grader see transcript text only, or text plus image? | Text only. One canonical answer; the image is shown beside the grade for one-tap correction and kept for contests. *Revised 2026-10-11: no confirm step before grading (§6.6)* |
| D8 | Capture processing semantics | **Decided (owner, 2026-10-11):** the daily-loop defaults C1–C3 (`docs/specs/daily_loop_frictionless_defaults.md`). Saving makes a reference; filing and verified solving happen silently; one tap adopts. M1 stores and routes manually; the background processor comes in M3 (T6) |
| D9 | Offline practice? | No. Practice needs the desktop online; capture works offline |
| D10 | Identity: require both the Tailscale login header and a device token, or the token only? | Both, always. The token identifies the device; the header is one comparison that only matters if a node is ever shared |
| D11 | Desktop asleep | Accept it in M1. Measure how often captures queue; then choose between a sleep inhibitor during sessions, Wake-on-LAN through an always-on node, or moving the host |
| D12 | Grant scope: only the phone, or all of the owner's devices? | **Decided (owner, 2026-10-11): no LearnLoop-specific policy.** The tailnet is single-user, and the owner wants general phone → desktop access anyway |
| D13 | Desktop UI for the inbox: a strip on Today, or a separate screen? | A strip on Today, with a count and one-click routes. A separate screen only if volume warrants it |
| D14 | HEIC input: reject it (the Shortcut converts to JPEG), or add `pillow-heif`? | Reject in M1; the Shortcut and the PWA convert to JPEG. Revisit if a capture path ever skips conversion |
| D15 | Host vault: one pinned vault, or follow the desktop's open vault? | Pinned in `mobile.toml`. The desktop shows a banner when they differ |
| D16 | Capture-scope tokens for the Shortcut | **Kept as built (revision 4, owner 2026-10-12).** The Shortcut gets a `capture` token; the PWA gets an `app` token |

---

## References

- [Serve] Tailscale Serve: https://tailscale.com/kb/1312/serve (identity headers; tagged-device and Funnel exclusions; the localhost recommendation limits forgery to local processes; ACLs apply)
- [Serve CLI] `tailscale serve` command reference: https://tailscale.com/kb/1242/tailscale-serve (`--bg` persistence, `status`, `reset`, `off`, the `http://127.0.0.1` proxy note)
- [Funnel] Tailscale Funnel: https://tailscale.com/kb/1223/funnel (off by default; the `funnel` node attribute; most-recent-command visibility)
- [Grants] https://tailscale.com/kb/1324/grants (`src`/`dst`/`ip` syntax, deny by default, matching rules combine)
- [VPN On Demand] https://tailscale.com/kb/1291/ios-vpn-on-demand (starting Tailscale automatically for `*.ts.net` hostnames; hostname matching needs the interface rule set to Do Nothing)
- Python `http.server`: https://docs.python.org/3/library/http.server.html ("only implements basic security checks")
- iOS share target status: WebKit bug 194593 (https://bugs.webkit.org/show_bug.cgi?id=194593), still open; https://firt.dev/notes/pwa-ios/ lists `share_target` as unsupported on iOS

*Related: `spec_image_dropin_ingest.md` · `spec_blind_grading_diagnosis_split_v1.md` · `spec_embedding_consumers_v1.md` §5 · `spec_project_understanding_v1.md` · [[User intentions]] · [[LearnLoop_User_Intentions_v2]]*
