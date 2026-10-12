# Mobile M1 — capture

## Implementation plan

1. Start `mobile/m1` from the primary checkout's `main`. Keep M1 independent
   of the parallel Slice A phases: no scheduling, grading, or practice changes.
2. Add shared capture storage, sanitized originals, atomic idempotent receipts,
   pairing/device credentials, and desktop routing. Assign the next free migration
   number at integration and regenerate the rollback-mode head fixture/reference.
3. Add the optional capture-only HTTP host with strict schema attach, loopback,
   identity/token/scope checks, bounded requests, pairing UI, and default-deny RPC.
4. Integrate the desktop Today inbox with existing card/source/tutor workflows;
   record routes only after successful backend operations. Add CLI inbox listing.
5. Ship deployment diagnostics, the user service, and phone capture/outbox setup.
6. Verify focused M1 gates, import contracts, full parallel Python suite,
   durability lane, and frontend typecheck/tests. Review integration and commit
   clear changes; do not merge or push.

## Validation boundary

Automated tests use fake identity headers and local test vaults, never a live
Tailscale service or the owner's working fixtures. Acceptance gates A1–A3 require
the owner's real phone and tailnet policy and will be recorded separately from
automated evidence. No personal configuration or provider credentials are read.

## Results

Implementation is on `mobile/m1`, based on primary `main`
`1a0f7a0a9047ce3357f524c3054c7bf1c20bb6b5`. No merge or push is requested.
Automated verification is green. Real-device acceptance remains open.

## Built

- `learnloop_mobile` and `learnloop-mobile`: `serve`, `pair`, `devices`,
  `revoke`, `inbox list`, and `doctor`. Exact mobile dependency pins, direct
  Pillow dependency, packaged pairing assets, and import-linter boundaries.
- Capture-only loopback host; exact schema-set check and exit 78; no sidecar,
  vault loader, ingest runner, migration, or primary startup maintenance.
  `/healthz`, `/api/v1/status`, `/pair`, capture receipt/status endpoints.
- Header-first Host/Origin/identity/bearer/scope checks, bounded headers/bodies/
  multipart/deadlines/admission (no per-device rate limit; only pairing attempts
  share a budget), separate serialized capture execution,
  retryable SQLite contention, no CORS, no-store responses, CSP, and no payload/
  secret access logs. All RPC methods are denied in M1, including future methods.
- Five-minute single-use pairing with fragment QR/manual code, hashed tokens,
  capture/app scopes, durable failed-exchange lock, immediate revocation and
  unclaimed-device expiry. Device authentication/listing are read-only; admitted
  mutations update last-seen at most once per minute.
- Shared `learnloop.capture`: globally unique ULID receipt idempotency across
  re-pairing; conflicting manifest/raw-media fingerprints rejected; HTTP(S)/arXiv
  references only; JPEG/PNG/WebP decode, orientation and metadata removal;
  no HEIC/audio input. Capture and initial route commit atomically.
- Migration 167: classified capture ledger/workflow tables, pairing attempt/
  lock accounting, durable route-recovery intent, purge deletion-retry flags,
  and receipt/route/dismiss timestamps. Head fixture renamed to
  `migration_head_167`, regenerated in rollback mode, references regenerated.
  No working-owner fixture was migrated, reverted, or committed.
- Desktop Today Inbox: mount/focus/30-second refresh, pinned-vault banner,
  existing card/Quick Add/tutor routes, image-to-card fallback with the photo
  shown beside the card editor, dismiss/purge, a paged handled view, and
  deletion failure/shared-original visibility. Destination IDs/receipts make
  route retries recover committed work rather than duplicate it; an unfinished
  save can be finished from its persisted request after a restart.
- `learnloop inbox list --vault PATH --json`, including handled entries with
  `--all`. Saving a phone capture creates only a reference; no automatic
  classification, provider call, practice adoption or scheduler write.
- Native iOS capture/photo/flush `.shortcut` assets, deterministic generator,
  import-time host/token setup, JPEG conversion and save-before-network outbox.
  Android HTTP-client instructions in `docs/mobile-shortcuts.md`.
- `deploy/learnloop-mobile.service`, disabled example `mobile.toml`, secret-free
  `mobile.env.example`, and read-only deployment doctor with fake-command tests.

## Decisions and deviations

1. **Spec revisions conflict.** The initial thread contained revision 2. Fetching
   primary `main` brought revision 3, which removes scopes/pairing/grants/Android.
   The explicit task still requires those features, so this implementation follows
   the revision-2 M1 scope (`git show a3c8a867:docs/specs/spec_mobile_tailnet_v1.md`).
   The revision-3 spec has not been overwritten.
2. **Native-only Shortcuts, explicitly chosen by the owner in this thread.**
   No Scriptable or companion app. Native HTTP actions cannot reliably classify
   status/transport failures, so automatic 401 stop/re-pair and 409 quarantine
   become visible fail-stop retention plus manual recovery. Files are saved
   before sending and deleted only after a parsed received receipt. The concrete
   path is iCloud Drive/Shortcuts/LearnLoop/outbox. The owner's expectation is that
   carson normally remains online. iCloud outbox storage is not tailnet-local.
3. **Phone acceptance is not simulated.** Assets are unsigned plist workflows.
   Signing/import, native parameter wiring, file-provider permissions and actual
   multipart serialization must be checked on the iPhone. Structural tests alone
   do not establish that A3 passes; no Apple signing/publication was performed.
4. **Original publication and purge share a short SQLite writer reservation.**
   Expensive image decoding/re-encoding happens before the transaction. Storing
   the already-sanitized bytes remains inside the publication reservation,
   unlike revision 2's store-before-transaction order, because that order races
   physical purge. Canonical-source registration uses the same reservation.
   Only file publication/fsync and SQL—not image decoding or AI—hold the lock.
5. **Purge preserves shared originals and already-created destinations.**
   It removes capture text/URL/note and route recovery payload, leaves a
   fingerprint tombstone, and removes unshared media. Another capture/source may
   still reference identical bytes; this is reported, not silently deleted.
   Interrupted/failed unlinks leave durable deletion-pending state and a retry.
   A running desktop operation may finish its already-started destination after
   purge, but cannot restore the purged inbox payload.
6. **Existing tutor API needs a source note.** Actual Ask send creates a
   deterministic reference-note anchor in the chosen existing subject. Cancel
   creates nothing. Provider failure leaves the capture new but may leave that
   reference note. A committed, incomplete tutor event is not automatically
   reissued, avoiding duplicate questions/provider spend; its recovery error
   is explicit.
7. **M1 status reports `grading_ready=false`.** It has no grading runtime.
   Doctor separately checks the unit's literal EnvironmentFile using the same
   shared grading-selection/readiness path, without a sidecar or provider call.
   The invoking shell's provider keys are not inherited into that check.
8. **Unidentifiable wrong pairing codes.** The exchange has no pairing-record
   selector. A wrong credential therefore charges every active record against
   its five-attempt limit. This conservative rule cannot evade the per-record
   cap. The global 20-failure/10-minute lock is persisted and only local `pair`
   clears it.
9. **Request-log bounds.** Only admitted mutations are persisted; rejected auth,
   rate-limit and busy traffic is not an unlimited SQLite/log write path.
   Retention pruning happens on admitted work, never host startup.

## Setup for the owner (not executed here)

Use a backup-API copy for initial setup, not a tracked working fixture.

```sh
uv sync --extra dev --extra mobile
uv run learnloop doctor --vault /ABSOLUTE/VAULT
```

Create `~/.config/learnloop/mobile.toml` from `deploy/mobile.toml.example`, set
the absolute pinned vault, carson's actual lowercase `.ts.net` hostname and the
owner login, then set `enabled=true`. This file does not follow the desktop's
currently selected vault.

Install `deploy/mobile.env.example` as `~/.config/learnloop/mobile.env` with
mode **0600**. M1 capture needs no provider key; supply any later keys locally,
never in this repository. If customizing `LEARNLOOP_CONFIG_DIR`, set it in the
unit EnvironmentFile as well. Replace the service's `/ABSOLUTE/PATH/learnanything`
with the installed checkout and install the unit under `~/.config/systemd/user/`.

```sh
systemctl --user daemon-reload
systemctl --user enable --now learnloop-mobile.service
tailscale serve --bg --https=443 http://127.0.0.1:8765
tailscale serve status --json
uv run learnloop-mobile doctor --json
```

Never use Funnel. Doctor verifies actual loopback listeners, that the exact
HTTPS Serve target is the only Serve route to the backend port (background,
foreground and Service configs; no TCP forwards), absence of Funnel on 443 and
on any backend route, schema/vault, env-file permissions, paired devices,
orphan originals and owner tailnet devices, and surfaces Tailscale health
warnings. It neither checks nor modifies tailnet policy (D12).
Grading can be unavailable without preventing M1 captures.

### Acceptance A1–A2, and an optional grant

Under D12 no LearnLoop-specific policy is needed. Doctor returns a phone-only
recipe as `optional_policy_example`, only for an owner who wants to narrow
access to this port; it is not part of acceptance:

```json
{
  "hosts": {
    "learnloop-phone": "<phone-tailnet-IP>",
    "learnloop-desktop": "<carson-tailnet-IP>",
    "learnloop-other": "<another-owner-device-tailnet-IP>"
  },
  "grants": [
    {"src": ["learnloop-phone"], "dst": ["learnloop-desktop"], "ip": ["tcp:443"]}
  ],
  "tests": [
    {"src": "learnloop-phone", "accept": ["learnloop-desktop:443"]},
    {"src": "learnloop-other", "deny": ["learnloop-desktop:443"]}
  ]
}
```

If used, grants are a union, so it narrows nothing while broader rules remain.
Keep the phone user-owned, not tagged, so Serve supplies identity. A1: make a
phone request with a fake login header and verify Serve replaces it with the
real owner identity. A2: `tailscale serve status --json` shows only the expected
443 → loopback mapping (doctor's `serve`/`funnel` checks), and the URL does not
resolve or connect from a device off the tailnet. These checks require the
owner's devices and have **not** run here.

### Pair and install native Shortcuts

```sh
uv run learnloop-mobile pair --label "iPhone Shortcut" --scope capture
uv run learnloop-mobile devices
```

Scan the QR or visit `/pair` on the phone and enter the manual code within five
minutes. Copy the once-returned capture token into the **installed private**
Flush Shortcut’s setup question; no shared asset contains it. Lost token
response: pair again; unclaimed devices expire after 24 hours.

Follow `docs/mobile-shortcuts.md` for signing/importing all three workflows and
creating the outbox folder. Configure Tailscale iOS VPN On Demand for `*.ts.net`
with its interface rule **Do Nothing**. Verify text, URL/arXiv and HEIC→JPEG
shares, then disable networking, share, reconnect and flush. Repeat a flush and
confirm one server capture. Test 401/409 retention before trusting the outbox.
This is acceptance **A3**, still pending. Revoke temporary test credentials:

```sh
uv run learnloop-mobile revoke DEVICE_ID
uv run learnloop inbox list --vault /ABSOLUTE/VAULT --all --json
```

Never share/export a configured Shortcut: its plaintext token travels with it.
On a lost phone, revoke its LearnLoop token and remove it from the tailnet.

## Verification

- Focused host/domain/doctor/coexistence validation after security review:
  **82 passed** (before final route-recovery tests).
- Migration/table roles/replayer/rebuild/shadow/embedding fixture checks:
  **78 passed**.
- Import contracts: **8 kept, 0 broken**.
- Native Shortcut structural checks: reproducible plist graph, save-before-send,
  receipt-gated deletion, timestamp direction and import-time setup; device
  execution remains unverified.
- Initial full run: **6208 passed, 17 failed**. Sixteen were integration setup:
  old/new fixture directories coexisted, fixture rename had not propagated,
  SQL-owner registrations and CLI snapshot needed updating. The remaining
  `test_span_view_renders_available_local_pdf_page` needed optional `pypdfium2`;
  installed into the test environment with `uv pip install pypdfium2` (no
  application dependency change). All these focused failures are resolved.
- Initial durability run: **65 passed, 1 failed**, solely the two-head-directory
  transition; resolved by finishing the fixture rename.
- Frontend final checks: `npm run typecheck` passed, `npm test` **37 passed**
  across nine files, and `npm run frontend:build` passed with the existing
  >500 KB bundle warning. `npm install` reported 14 dependency audit findings
  (4 low, 2 moderate, 6 high, 2 critical); no forced dependency upgrades were
  made as part of this milestone.
- A real `learnloop-mobile serve`/uvicorn subprocess smoke test on an ephemeral
  loopback port passed health/status, first capture 201, retry 200 with identical
  receipt, exactly one committed inbox row, graceful shutdown, and no token/
  pairing secret in server logs. It used a temporary test vault and **fake**
  Serve identity headers; this does not substitute for A1.
- Additional Rust check was attempted but the machine's compiler cannot start:

  ```text
  cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml
  error: process didn't exit successfully: `rustc -vV` (exit status: 127)
  rustc: symbol lookup error: /usr/lib/librustc_driver-b9ead9e03832c46d.so:
  undefined symbol: _ZNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEE9_M_mutateEmmPKcm,
  version LLVM_23.1
  ```

  No system toolchain was modified. Frontend checks above passed; native shell
  compilation needs a working Rust/LLVM installation.
- **Final frozen-tree full suite:** `uv run pytest -n auto` —
  **6268 passed, 46 warnings**, 168.80 s. No failures. Log retained locally in
  `.pytest_tmp/mobile-final-full.log`.
- **Final durability lane:** `uv run pytest -m durability` —
  **66 passed, 6202 deselected, 1 warning**, 41.11 s. No failures. Log retained
  locally in `.pytest_tmp/mobile-final-durability.log`.
- Warnings are Starlette's deprecated httpx TestClient compatibility and the
  existing Python 3.12 datetime-adapter / multithreaded-fork warnings.
- `uv build --wheel` passed; archive inspection confirmed the mobile package,
  capture package, pairing HTML/JS and console-script entrypoint are included.
- Final `git diff --check` passed; owner working fixtures remain untouched.

### Commits

1. `3fde02bf` — Add durable capture inbox, scoped pairing, and M1 schema.
2. `73faf42a` — Serve bounded tailnet-only captures with pairing and diagnostics.
3. `8a93d086` — Route desktop inbox captures through recoverable authoring workflows.
4. `4a62d533` — Ship native iOS capture and flush Shortcut workflows.
5. This review report records the final verification and deployment boundary.

## Rollout report and open acceptance

No real captures or phone usage were collected. The two-week rollout therefore
has **N=0**, no capture rate, routed/dismissed share or time-to-route estimate,
and no measured Shortcut flush/failure rate. `received_at`, `routed_at`,
`dismissed_at`, device and route states support the eventual inbox aggregates;
admitted HTTP results are available without payloads in `mobile_request_log`.
Native outbox flush counts/failures require owner observations, not fabricated
server-side estimates.

- A1, A2 and A3 are owner checks and remain unverified. Do not proceed to M2 on
  the strength of automated tests alone.
- Confirm whether the explicitly requested revision-2 security/pairing workflow
  should remain, or whether a separate change should adopt revision 3.
- Before integration with parallel Slice A phases, rebase onto merged main,
  recheck the next free migration number, regenerate the head fixture/reference,
  and rerun table roles, replay/rebuild equivalence and durability. Migration 167
  is free at the latest fetch, but is not reserved across other branches.
  The final fetch observed primary `main` at `be33cdd0` (daily-loop fixes), with
  no added migration. Those later commits are **not** included in this branch's
  validation; overlapping files include Today and item authoring. No history was
  rewritten or merged to pull them into this completed M1 work.
