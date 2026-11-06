# Phone v2, stage V1: the shell and its plumbing

**Spec:** `docs/specs/spec_mobile_frontend_v2.md` §8's V1 row (detail in §1, §4, §5, §6.1, §7). **Branch:** `phone/v1-shell`, from main `1c12763372` (the owner's M2a follow-ups: `submit_eliciting_response`, the diagnosis card, the Shortcuts' capture id). **No migration, no successor, no model call, no new dependency.**

The rule for this stage was that today's phone behaves exactly as before: the same requests with the same parameters, the same outbox, the same host replies. Two things show it held:
- `App.test.tsx`'s 149 cases, M2a's journeys through a fake host, pass on the new shell. One copy line changed (§2, item 9).
- The request contract (§1.3) records every request today's wrappers send and runs each through the host's own checks.

## Commits

| Commit | What |
|---|---|
| `7b11b0d67c` | Host: `GET /api/v1/meta`, `Server-Timing`, the phone's round trips in the request log and the report, the generated client files, the request and reply contract |
| `d25e3d1195` | PWA: the shell (places, stacks, sheets, fragment), themes, Dynamic Type, accessibility, connection states, the stale-app reload, the generalized outbox, the display cache, the build-keyed service worker; Today, Question, Feedback and Capture restyled |
| `2371dc6d3c` | Tests: the frame's back chevron and edge swipe, the keyboard inset, the service worker's build stamp |
| (this commit) | This review, the spec's "As built" note, the regenerated module reference |

## 1. What was built

### 1.1 Host (`src/learnloop_mobile/`, `src/learnloop/capture/`)

- **`GET /api/v1/meta`** (`host.py`). Auth is `Token(app)`, and the call is not logged. It returns `{host_version, api_version: 1, allowlist_digest, schema_version}`.
  - `allowlist_digest()` (`allowlist.py`) hashes each method's name, kind and retry policy, plus the API generation. The constraints belong to the host, so a stricter constraint does not force a phone reload.
  - `schema_version` is the head migration. `attach()` already checks that the applied migrations are exactly those.
- **`Server-Timing` on every `/rpc` reply**, including refusals (403, 401, 422, 400):
  - `queue;dur` and `handler;dur` for a short method, measured on the RPC worker (`runtime.call_short(timing=…)`);
  - `job;dur` for a long method (the time `/rpc` held it, up to its 15 s wait);
  - `total;dur` always.
- **The phone's round trip goes into the existing request log.**
  - The phone sends its last `/rpc`'s time on its next `/rpc`, in the `LearnLoop-Client-Timing` header as `<method>;status=<n>;dur=<ms>[;host=<ms>]`, where `host` is the `Server-Timing` total it read.
  - The host logs two rows in `mobile_request_log.duration_ms`: `client:<method>` (the round trip) and `network:<method>` (that minus the host total).
  - Only an allowlisted method name is logged. A header that does not parse is ignored, never refused. `capture/maintenance.py`'s label rule now admits the two prefixes.
- **`learnloop-mobile report` → `round_trips`**:
  - per method: p50 and p95 of the host's own time (`rpc:`), the round trip (`client:`) and the network (`network:`);
  - `network_share` (median network over median round trip);
  - for short methods, `within_short_read_budget`, against §4.5's 1 s p50 `keep` bound. The report shows it and nothing enforces it.
- **Generated client files** (`client_contract.py`): `retryPolicy.json` and `phoneMethods.ts` (the method list, `PhoneMethod`, `LONG_METHODS`, `ALLOWLIST_DIGEST`). `retryPolicy.json` came out byte-identical to the hand-kept copy.

### 1.2 PWA (`apps/learnloop-mobile/`)

- **`shell/`**:
  - `TabBar`: Today · Read · + · Progress. The + is announced as "Capture", and `aria-current` marks the current place.
  - `ScreenFrame`: the top bar with the back chevron, the edge swipe back, focus moved to the new screen, and its title announced in a polite live region.
  - `Sheet`: opens from the bottom, traps focus and returns it, closes on Escape, its button, the backdrop, or a downward swipe on the handle past a quarter of its height.
  - `ConnectionLine`, `DisplaySheet`.
  - `navigation.ts` (the fragment and a stack reducer), `connection.ts` (the four states plus stale), `freshness.ts` (the meta check and the reload), `theme.ts`, `viewport.ts` (the keyboard inset from `visualViewport`), `swBuild.ts`.
- **Places and stacks (§4.2):**
  - Question, Feedback and the grading wait cover the tab bar.
  - The current place and path are mirrored in `#/…` with `replaceState`, and a cold start opens the same place.
- **Themes (§4.6):**
  - Dark is today's palette. Light is warm paper (`#f7f4ee` and `#1f1d1a`, with a deeper amber `#8a4f0f`).
  - The system's choice applies unless the Display sheet overrides it.
  - All sizes are rem on a `-apple-system-body` root, so Dynamic Type scales everything and rows wrap.
- **Connection states (§4.4):**
  - *Desktop offline. Capture still works.*, with M2a's count of captures waiting to send.
  - *Desktop is busy — trying again.*
  - *Grading isn't available right now. Your answer is saved.*
  - *LearnLoop was updated.* with **Reload**.
  - Each shows as one quiet line under the top bar.
  - **Back from offline** (the first host answer after offline, or the `online` event), in this order: flush the outbox, re-read the session (`session_moved`), read the token. Today refreshes through its token, as before, so nothing refreshes under an answer being typed.
- **The stale-app path (§5.2):**
  - The app compares `/api/v1/meta`'s digest with its build's on open and on every return to visible.
  - A mismatch, or any `method_not_allowed`, shows the line, never the raw refusal.
  - **Reload** asks the service worker for an update and reloads. The worker fetches the shell network-first.
  - `sw.js`'s cache is now `learnloop-shell-<build hash>`. The build stamps it with the hash of the built `index.html`, so every build installs a new worker, whose `activate` drops the old cache.
- **`http.ts`**:
  - `call`, `rpcOnce`, `rpcOutcome` and `runLong` take a `PhoneMethod`, so a screen that names a method the allowlist lacks fails typecheck.
  - It reads `Server-Timing`, carries the round trip on the next `/rpc`, and reports to the connection line.
  - Retry, the 202 path, the 401 rule and `OFFLINE` are unchanged, and the 401 now also clears the display cache.
- **The outbox, generalized (§5.4):**
  - `IntentKind` defines how a kind is listed, sent and settled. §7's response classes are shared (`responseClass`), and every kind is flushed together in client-id order.
  - V1 registers only the capture (`CAPTURE_INTENT`), with its store, its request and its key unchanged.
- **The display cache (§5.4):**
  - It is a new IndexedDB store (database version 2). The upgrade from version 1 keeps the token and every waiting capture, which a test opens a real v1 database to check.
  - Reader sections live in an LRU bounded at §5.4's 50 MB. A new revision of an extraction drops that extraction's older sections.
  - The plan and lessons keep only their latest copy.
  - A 401 wipes it.
  - Nothing reads it yet: V2 and V4 do.
- **Restyled, behaviour unchanged:**
  - The screens moved to `today/`, `practice/`, `capture/` and `pair/`.
  - One primary action sits full width in a sticky thumb zone: Next, Submit, Save, Pair.
  - The symbol bar sits above Submit in that zone.
  - The other actions wrap beneath it.
  - The diagnosis card and the eliciting questions are kept as they were. Their Send buttons became secondary, since Next is the screen's one primary action.
  - Read and Progress say plainly that they come in a later update.

### 1.3 Tests added

- **pytest**
  - `tests/test_mobile_meta_timing.py` (23): meta and its auth; `Server-Timing` on replies and refusals; the timing header parser; the `client:`/`network:` rows; the report table.
  - `tests/test_mobile_phone_contract.py` (8):
    - the generated files match the allowlist;
    - `phone.ts` names only allowlisted methods;
    - each recorded request passes `validate_envelope`, `check_parameters` and the method's `ParamsModel` (`extra="forbid"`), and a long method carries its `request_id`;
    - a real host journey on a fresh vault, with the fake grader, asserts each reply has the fields the screens read (§2, item 10).
- **vitest**
  - `src/api/contract.test.ts`: records every wrapper's requests into `contract/<method>.json` and checks every wrapper has examples.
  - `src/api/timing.test.ts`: `Server-Timing`, the round trip, the connection states.
  - `src/desktopImports.test.ts`: the `@desktop` module walk.
    - It is not vacuous: §5.3's shared modules are in the walk, and the desktop's own `api/client.ts` is caught.
  - `src/shell/{navigation,theme,Sheet,ScreenFrame,Shell,a11y}.test.*`:
    - `theme`: AA contrast for nine text pairs in each theme, read from `styles.css` itself;
    - `a11y`: the desktop's deny-list (imported) and a named-control check over every phone surface and today's practice, and KaTeX's MathML;
    - `Shell`: places, the fragment, covering, the Display sheet, the connection states, the reconnect order, and the stale reload.
  - `src/store/displayCache.test.ts`, plus new cases in `src/store/outbox.test.ts`.

## 2. Where the spec was not built as written, and the smallest way to finish

1. **The fragment does not reopen a question or a feedback.**
   - What §4.2 says: "A reload or a cold app start returns to the same place."
   - What V1 does: the place and the path are mirrored and restored, but a question or a feedback is never reopened from the address. Opening a question is its serve (an offer and a presentation), and opening a feedback records an open.
   - Why: the open question with a draft, and a submit left mid-grade, already come back from the checkpoint and the pending submit, as M2a built it. A test pins that a reload on `#/today/question/i1` serves nothing.
   - Smallest finish: V2 reopens a feedback from the fragment with `get_feedback{recordOpen: false}`.
2. **Feedback and the grading wait have no back chevron.** M2a had no way back from either except Next. Adding one would have been a new path, and V1 keeps today's behaviour. The Question has the chevron ("Back to Today"), which does what its Back button already did. Smallest finish: V2 adds it to Feedback along with the rest of its rework.
3. **Capture in the top bar of covering screens.** §4.2 puts Capture in the tab bar and has Question cover the tab bar. M2a let the learner capture mid-question with the question kept mounted (no second serve, a `F5` test). The top bar's **+** keeps that ability. It opens a place and commits nothing, so §4.3's top-corner rule holds.
4. **Read and Progress are honest placeholders** until V4 and V7, so the four places sit where they will stay.
5. **The desktop's palette is not imported.**
   - What §4.6 says: import the desktop's colour values if its tokens are already CSS variables.
   - Why not: they are (`apps/learnloop-tauri/src/styles/palettes.css`), but their values (a `#282a36` family) are not the phone's dark palette, which §4.6 fixes as today's.
   - So the phone keeps its own small set, which is §4.6's other branch.
6. **The round trip rides on the next request.**
   - What §4.5 says: the PWA records its round-trip time beside the host's in `mobile_request_log`'s existing duration field.
   - How: with no migration and no new endpoint, the sample travels on the next `/rpc` and becomes `client:`/`network:` rows.
   - The cost: one sample is held at a time, so a sample is lost when the app closes, or when two calls finish before the next one goes out. The report says so in a note.
7. **"pytest writes the generated files".** The pytest fails on a difference, and rewrites the files only under `LEARNLOOP_UPDATE_PHONE_CONTRACT=1`. The vitest that records `contract/*.json` works the same way. This keeps a gate on a merged tree from silently rewriting its own evidence.
8. **The offline line says "Capture still works."** It does not say "Reading and capture still work", because there is no phone reader before V4. M2a's count of captures waiting to send is kept: it explains an absence, as the waiting-for-the-desktop count does.
9. **One copy line changed.** The pairing screen's "Scan a new token to send 1 capture." is now "Pair again to send 1 waiting capture." "token" is on the desktop's deny-list, and an installed app pairs with the code, not a scan.
10. **One reply is checked elsewhere.**
    - The host journey cannot produce `submit_eliciting_response`'s reply without a diagnosis model's open causal factor.
    - Its contract file names the tests that pin `admissibleAsIndependent`: `tests/test_dialogue_causal_join.py` and `tests/test_ux_phase4_feedback.py`. The contract test fails if any other method goes unchecked.
    - The journey does reach `answer_grading_clarification` through the host, as a job, by inserting a pending clarification.
11. **`App.test.tsx` is kept whole** rather than split by journey (§6.1). Its 149 unchanged cases are this stage's proof of unchanged behaviour. Smallest finish: V2, which rewrites Today and Feedback, moves its `describe` blocks to `today/` and `practice/` with a shared fake host.
12. **When the grading line shows,** the question's own failure line ("AI grading is unavailable; your answer is saved…") also stays. That is M2a's per-action error, with its *Try again*. V2 can drop one of the two when it reworks the question.
13. **UI thresholds.** The sheet's quarter-height swipe, and the edge swipe's 20 px zone across a third of the screen (iOS's own edge-gesture zone), are interaction constants, not parameters. No config key was added, so `parameter_registry.py` is unchanged. The 50 MB section bound and the 1 s short-read budget are §4.5 and §5.4's declared `keep` bounds.

## 3. Persisted and served meaning

- No table, column or migration.
- `mobile_request_log` gains two endpoint label families, `client:<method>` and `network:<method>`. They are pruned at 90 days like every row there, and read only by the report.
- Nothing that serves, grades or schedules reads the log, so no successor is needed (`docs/algorithm-change-playbook.md`: no persisted meaning changed).
- Desktop replies are untouched: the sidecar is not edited.

## 4. Security notes for review

- **New endpoint:** `/api/v1/meta` is a `Token(app)` GET behind the same Host, identity and origin checks. It tells a paired device the host version, the schema head and the allowlist digest, and nothing from the vault.
- **`Server-Timing`** is same-origin with no CORS, and carries timings only.
- **The timing header** is parsed by one strict full-match pattern. Its method must be in `ALLOWLIST`, so nothing arbitrary reaches the log. It is read only after the token is checked, and a bad value costs the request nothing.
- **Unchanged:** the allowlist (and so the digest's inputs), the CSP, and the service worker's scope (`/app/` only, never `/rpc` or `/api`).

## 5. Gate (this step; the full suite runs once in the landing gate)

Run in the worktree, each pytest and vitest command inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, with pytest at `-n 6` and vitest at `--maxWorkers=4`.

- **Setup:** `uv sync --extra dev --extra mobile`, then `uv pip install --offline pypdfium2==5.14.0`; `npm install --prefer-offline` in `apps/learnloop-mobile`.
- **`uv run lint-imports --no-cache`** (under `env -i`, with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`): **43 kept, 0 broken**, the frozen deferred cycles contract included.
- **`pytest -n 6 tests/test_mobile_*.py`** (every mobile host test, the two new ones included): **651 passed**, none skipped (the mobile extra is installed).
- **`pytest -n 6 tests/test_mobile_phone_contract.py`**: **8 passed**. It also ran inside the run above.
- **The contract set:** **495 passed**:
  - `pytest -n 6 tests/test_sidecar_measurement.py` (display-label audit), `tests/test_codex_lockdown_round3.py` (process-launch allowlist) and `tests/test_codex_lockdown_frozen.py`;
  - `tests/test_cli_help_snapshot.py`, `tests/test_architecture.py`, `tests/test_table_roles.py` and `tests/test_coordinated_migrations.py`;
  - `tests/test_tracked_fixture_databases.py`, `tests/test_desktop_rpc_contract.py`, `tests/test_mobile_allowlist.py` and `tests/test_sidecar_serializer_snapshot.py`;
  - `tests/test_config_refactor.py` (config defaults), `tests/test_public_tip_guards.py` and `tests/test_sqlite_file_copies.py`;
  - `tests/test_figures_prefetch_boundary.py` and `tests/test_module_catalog_inventory.py`.
- **`apps/learnloop-mobile`**:
  - `npx tsc --noEmit` (`npm run typecheck`): clean.
  - `npx vitest run --maxWorkers=4`, over every phone test file, all of which exercise something this stage touched: **16 files, 245 tests passed**. These are `App.test.tsx` (149, unchanged but one copy line), `api/{http,timing,contract}.test.ts`, `store/{outbox,displayCache}.test.ts`, `shell/{navigation,theme,Sheet,ScreenFrame,Shell,a11y}.test.*`, `desktopImports.test.ts`, `sw.test.ts` and `util/{attemptType,ulid}.test.ts`.
  - `npm run build`: built. The emitted `sw.js` carries `const BUILD = "<16 hex>"`. The build output is the gitignored `src/learnloop_mobile/static/app/`.
- **References:**
  - `module_generate.py`, then `module_validate.py`: **PASS**.
  - `validate_vault.py`: passed. `desktop_validate.py`: passed (no desktop file changed).
  - Provenance-only churn from main in `teacher/*` and `content/*` notes was left out.
- **Not run:**
  - `npm run frontend:build` in `apps/learnloop-tauri`, and `cargo check`: no file under `apps/learnloop-tauri` changed. The phone only imports its modules, which the import walk and the phone's own typecheck and build cover.
  - The durability lane: no DB, connection or migration code changed.
  - No paid or live call was made. V1 adds no model request.

**Test files run, for reading the landing gate against:**
- `tests/test_mobile_*.py` (all), including the new `tests/test_mobile_meta_timing.py` and `tests/test_mobile_phone_contract.py`.
- The contract set listed above.
- Every vitest file in `apps/learnloop-mobile/src` and `public`.

**A process note:** while editing `host.py`, one small text-replacement script ran with plain `python3`, outside `env -i`. It only rewrote that file's text (imports and two constants) and imported nothing from LearnLoop. Every later patch used the editor, and every later CLI or Python call ran under `env -i` with empty homes.

## 6. What the owner runs on the iPhone (P1, P2)

Nothing below has been run on a device. M2a's A4 was never rendered in a real browser either (its known limit 3), so P1 is also the first real look at the editor and the symbol bar.

On carson, after landing. V1 adds no Python dependency and no migration, so only the app is rebuilt and the host restarted:

```bash
cd ~/Documents/thinking/learnanything
(cd apps/learnloop-mobile && npm install && npm run build)
systemctl --user restart learnloop-mobile
.venv/bin/learnloop-mobile doctor
```

- **P1. The new shell, themes, text size, VoiceOver.**
  1. Close the home-screen app from the app switcher and open it again. The new shell opens, with the tab bar Today · Read · + · Progress.
     - If the old screen persists after a second reopen, delete the home-screen icon and add it again from Safari (`https://HOST/app/`, Share, Add to Home Screen).
     - Then pair with `.venv/bin/learnloop-mobile pair --label "iPhone" --scope app` and its manual code. The outbox survives either way.
  2. Switch iOS Appearance between Light and Dark in Control Centre: the app follows. Open **Aa** (Display), choose Light, then Dark: the choice holds against the system's. Choose "Match the phone" to go back.
  3. Settings → Accessibility → Display & Text Size → Larger Text, turned on and set to the largest size. Reopen the app: text is large, and no button is clipped. Next, Submit, the tab labels and the symbol bar wrap or scroll; none are cut off. Set it back.
  4. Turn VoiceOver on. Swipe through the tab bar: it reads "Today, selected", "Read", "Capture", "Progress". Begin a session and open a question whose prompt has math: VoiceOver reads the formula as math, not as KaTeX's characters. Double-tap "Back to Today": the new screen is announced.
  5. Answer one question end to end, as before. Submit sits above the keyboard with the symbol bar while typing. Feedback, the diagnosis card and its questions behave as they did.
  6. `.venv/bin/learnloop-mobile report`: `round_trips.methods` lists the methods just used, with `round_trip_ms` counts above zero and a `network_share`.
- **P2. Offline, then back.**
  1. `systemctl suspend` on carson. Open the app from the home screen: it opens from the cache and says *Desktop offline. Capture still works.*
  2. Tap **+**, save a note. It says *Saved.*, and the line counts *1 capture waiting to send.*
  3. Wake carson. Return to the app, or wait up to a minute: the line clears and the capture is sent. Check with `.venv/bin/learnloop-mobile inbox list`.

## 7. Open questions

1. Should the Feedback screen get the back chevron in V2? It is item 2 above. The spec says yes; V1 kept M2a's "Next only".
2. Should the top bar's **+** on covering screens stay after V2, or should the tab bar's + be the only way to Capture? It is item 3. Keeping it costs nothing and keeps mid-question capture.

## Landing onto main

Main was `1c12763372`, the stage's base. It did not move while the landing ran (checked before the smoke and again before this commit), so there was no merge. No migration, no successor, no new dependency.

### Orchestrator rulings (verbatim)

- R1: "Codex's F1-F3 and the reconnect-order fix are accepted on the builder's failing-first tests; no further Codex round for V1 (UI-only, no new capability, no new RPC)."
- R2: "Open questions: Feedback gets the back chevron in V2, as the spec's 'one swipe or chevron returns' says (V1 keeps M2a's 'Next only'); the top-bar + (Capture) on Question and Feedback stays after V2, so capturing mid-question never serves the question again."
- R3: "The narrowings recorded by the builder (no reopen from the fragment, placeholders for Read and Progress, the phone's own palette, generated files only under LEARNLOOP_UPDATE_PHONE_CONTRACT=1, App.test.tsx split deferred to V2, the pairing copy change) are accepted for V1; V2-V4 pick them up."

R2 answers §7's two open questions: Feedback gets the chevron in V2, and the top bar's **+** stays.

### Gate

The gate ran at `5a03164763`. Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`; the full suite ran in 10G/2G under `flock /tmp/learnloop-fullsuite.lock`. Every other Python or CLI ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, with one exception (the process note below). No model call or paid call was made.

| Command | Result |
|---|---|
| Step 2: `tests/test_mobile_*.py` (15 files), `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_measurement` (display-label audit), `test_cli_help_snapshot`, `test_architecture`, `test_codex_lockdown_round3`, `test_public_tip_guards`, `-n 6` | 716 passed |
| Step 2: `lint-imports --no-cache` | 43 kept, 0 broken |
| Step 2: phone app: typecheck, whole vitest (`--maxWorkers=4`), `npm run build` | ok; 16 files, 256 passed; built |
| Step 3: `module_generate` / `module_validate` | PASS (1247 module notes) |
| Step 3: `desktop_generate` / `desktop_validate` | passed (321 TS/TSX + 6 Rust); nothing moved |
| Step 3: `validate_vault.py` | passed (2238 notes, all reachable) |
| References moved | 7 module notes, provenance only (`source_commit`, timestamps, worktree state): `content/_package`, `content/authoring/{_package,practice_leakage}`, `teacher/{_package,guards,probes,service}`. Main's copies had been generated from an uncommitted workspace at the exam-question guard's landing. Regenerated from the committed tree, they read `clean`. Committed with this record |
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Full pytest (`-n 8 --dist worksteal`) | **29873 passed, 90 skipped, 47 xfailed, 0 failed** (1:00:41) |
| Durability lane (`-m durability`), with the mobile host's two-process tests (`test_mobile_two_process`, `test_mobile_host_coexistence`, `test_mobile_pairing`) | 404 passed, 1 skipped (the owner-lane WAL test) |
| Owner lane on fresh backup-API copies of `owner-copies-mvp035` | 83 passed, 4 skipped, and the 2 known failures (`test_activity_backfill`, `test_placement_fixture_copies[arxiv_v2]`) |
| Desktop: typecheck, whole vitest (`--maxWorkers=4`), `frontend:build` | ok; 274 files, 2772 passed; ok |
| Desktop: `cargo check` | not run: no file under `apps/learnloop-tauri` changed |
| Phone: typecheck, whole vitest, build (again, in the gate) | ok; 256 passed; built |

**A process note.** One stdlib `python3 -c` ran outside `env -i`. It printed which keys of `tests/cli_help_snapshot.json` name `upgrade`, and it imported nothing from LearnLoop. Every other Python or CLI call ran under the wrapper.

### Smoke

The smoke started from fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy` (the owner's three vaults at mvp-0.43). In each copy's `learnloop.toml`, every `base_url` was set to `http://127.0.0.1:9`. Each copy was upgraded on main's code (`git archive` of `1c12763372`, with its `migrations/`) to main's latest tag, **mvp-0.52** (migration 249). Each journey then ran on a further fresh copy, one for main's code and one for the branch's.

**The host.** The real ASGI app from `learnloop_mobile.host.create_app`, run in-process through Starlette's `TestClient`, which binds no socket.
- **Pairing:** the phone was paired by the real exchange (`create_pairing` and `exchange_pairing`, scope `app`) and sent the identity header that Serve adds.
- **Grader:** the tests' in-process fake (`CountingGrader`).
- **The clock**, the one other seam: both trees ran with the wall clock frozen at `2026-11-07T00:00:00Z` (`datetime.now`, `utcnow` and `today`, as freezegun freezes them) and with deterministic ULIDs. That way the replies that read the clock (forgetting risk, due times) compare exactly. A first trial without the freeze differed only in those clock-derived floats.
- **Audit hook:** it refused any non-loopback connect or bind and any Codex process; its self-test refused both.

**The script, as the PWA sends it** (the wrappers' parameters from `contract/*.json`; each `/rpc` after the first carries `LearnLoop-Client-Timing`):
- `GET /api/v1/meta` (left out of the comparison), `/api/v1/status`;
- an eliciting answer (`submit_eliciting_response`) on the vault's open causal factor, while it is open;
- `start_session`: on `linear_algebra` and `probability`, a 409 `session_open_elsewhere`, then "Start here instead" with `replace`;
- `get_session`, `get_today_queue`, `/api/v1/queue-revision`;
- `get_practice_item`, `get_probe_contract`, `save_practice_draft`, `submit_attempt`, `/api/v1/submissions/{id}`, `acknowledge_practice_submission`;
- `get_feedback` (`recordOpen: true`), `get_grading_clarification`;
- after 8 s, `diagnosis_status` (the card) and `get_feedback` (`recordOpen: false`);
- a capture through the outbox's request (`POST /api/v1/capture`), the same record again (a retry), and `GET /api/v1/capture/{id}`;
- a second eliciting answer (on the vault's factor, or on the smoke's own attempt where the vault has none);
- the next item's `get_practice_item` and `skip_practice_item`, then `end_session`;
- every registry method outside the allowlist.

| Check | `linear_algebra` | `probability` | `arxiv_v2` |
|---|---|---|---|
| Requests and replies, main vs branch (status, content type, body; `Server-Timing` aside) | identical, 24 steps, 200,839 bytes | identical, 24 steps, 296,298 bytes | identical, 22 steps, 145,331 bytes |
| `Server-Timing` | on every branch `/rpc` reply (18 of 18); never on main's | 18 of 18; never on main's | 16 of 16; never on main's |
| `GET /api/v1/meta` | branch 200 `{host_version 0.1.0, api_version 1, allowlist_digest 9d84d218..., schema_version 249}`; main 404 | the same | the same |
| Today | 20 rows | 20 rows | 20 rows |
| Submit, feedback, card | 200 (within the 15 s window); score 0/4; card `pending`, `cardEnabled` true (the diagnoser's route is 127.0.0.1:9) | the same | the same, 0/7 |
| Capture | 201 `received`, retry 200 `received`, status 200 | the same | the same |
| Eliciting answer | 200, `admissibleAsIndependent` true; the second, on the same factor, 200 | the same | no open factor in the vault: `invalid_eliciting_response` on both trees |
| Methods outside the allowlist | 481 of 481 refused 403 on both trees | the same | the same |
| New `model_call_receipts` | 2 on each tree, both the fake's (`provider = fake`: `blind_grading`, `blind_grading:fake_turn`); 1 grade | the same | the same |
| Sockets and processes | no TCP connect or bind at all; one process on both trees, `git rev-parse HEAD` (data capture's version stamp); no Codex start except the self-test's refused one | the same | the same |

**The stale-app path.** The meta digest equals `ALLOWLIST_DIGEST` in `apps/learnloop-mobile/src/api/phoneMethods.ts` and in the built bundle. The UI side, where a host on another digest offers **Reload**, is covered by `Shell.test.tsx` "a host on another allowlist offers one tap to reload", which passed in the gate.

**`learnloop-mobile report`** ran with the branch's CLI on the branch's `linear_algebra` copy after the journey.
- It shows `round_trips.methods`, with per-method `host_ms`, `round_trip_ms`, `network_ms`, `network_share` and `within_short_read_budget`. For example, `get_feedback` has 2 round trips, p50 353 ms.
- `end_session` has no round trip, as expected: no `/rpc` followed it to carry the sample (§2 item 6).
- In-process, "network" is near 0.

The host instances ran in-process and exited with their scripts. Every copy (base, runs, main's archive, the owner lane) was deleted afterwards. The live phone host and its units were not touched.

What this can't show: Serve, a real phone, iOS storage and a real grader. P1 and P2 cover those.

### What the owner does

V1 adds no Python dependency and no migration, so the vaults need nothing.

(a) Rebuild the phone PWA and restart the phone host, on carson:

```bash
cd ~/Documents/thinking/learnanything
(cd apps/learnloop-mobile && npm install && npm run build)
systemctl --user restart learnloop-mobile
.venv/bin/learnloop-mobile doctor
```

(b) Run P1 and P2 on the iPhone (§6 above, copied here). This is also the first real-device look at M2a's editor and symbol bar (M2a's A4): nothing in M2a or V1 has been rendered on a phone yet.

- **P1. The new shell, themes, text size, VoiceOver.**
  1. Close the home-screen app from the app switcher and open it again. The new shell opens, with the tab bar Today · Read · + · Progress.
     - If the old screen persists after a second reopen, delete the home-screen icon and add it again from Safari (`https://HOST/app/`, Share, Add to Home Screen).
     - Then pair with `.venv/bin/learnloop-mobile pair --label "iPhone" --scope app` and its manual code. The outbox survives either way.
  2. Switch iOS Appearance between Light and Dark in Control Centre: the app follows. Open **Aa** (Display), choose Light, then Dark: the choice holds against the system's. Choose "Match the phone" to go back.
  3. Settings → Accessibility → Display & Text Size → Larger Text, turned on and set to the largest size. Reopen the app: text is large, and no button is clipped. Next, Submit, the tab labels and the symbol bar wrap or scroll; none are cut off. Set it back.
  4. Turn VoiceOver on. Swipe through the tab bar: it reads "Today, selected", "Read", "Capture", "Progress". Begin a session and open a question whose prompt has math: VoiceOver reads the formula as math, not as KaTeX's characters. Double-tap "Back to Today": the new screen is announced.
  5. Answer one question end to end, as before. Submit sits above the keyboard with the symbol bar while typing. Feedback, the diagnosis card and its questions behave as they did.
  6. `.venv/bin/learnloop-mobile report`: `round_trips.methods` lists the methods just used, with `round_trip_ms` counts above zero and a `network_share`.
- **P2. Offline, then back.**
  1. `systemctl suspend` on carson. Open the app from the home screen: it opens from the cache and says *Desktop offline. Capture still works.*
  2. Tap **+**, save a note. It says *Saved.*, and the line counts *1 capture waiting to send.*
  3. Wake carson. Return to the app, or wait up to a minute: the line clears and the capture is sent. Check with `.venv/bin/learnloop-mobile inbox list`.

### Open items

- V2 takes R2 (Feedback's chevron) and R3's narrowings (reopening a feedback from the fragment, splitting `App.test.tsx`, dropping one of the two grading-unavailable lines).
- In the smoke's in-process round trips, almost everything falls under the host's total, so the report's `network_share` is near 0 there. Only the iPhone (P1 step 6) gives a real network share.
