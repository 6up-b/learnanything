# Reader RW5d P2 sketch compartment: Codex review and fix round

Review: Codex (gpt-6.1-sol), job `20261101-152432-JprBcG`, on the stage tip `d47f521793`. One finding (Medium), no
High. Codex changed no files and launched no GUI; its own vitest run was blocked by the systemd user bus, so it
executed no tests. This round launched no GUI either and made no model or network calls.

## Review

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Shell frame guard trusts a caller-controlled referrer | **fixed** (the omitted-Referer and unexpected-origin halves); the replaced same-origin Referer half **rejected as not fixable at this layer, gap pinned** | `f76a8de7a6` | Rust `frame_guard::tests::omitted_headers_and_unexpected_origins_are_refused` (failed before the fix on `(Some("tauri://localhost"), None)`, passes after) and `a_replaced_same_origin_referrer_is_not_this_layers_to_catch` |

### F1 in detail

**Reproduced.** A new Rust test fed the guard the headers an app-origin Worker sends with `fetch(url, {referrer: ""})`
(Origin `tauri://localhost`, no Referer). Before the fix `refusal` returned `None`, and the existing test listed that
pair as allowed. The guard also accepted any Origin other than `null` (`https://example.com`, `ipc://localhost`, an
Origin whose Referer is on a different origin) and a request with no Origin at all.

**Fixed (`frame_guard.rs`):** the guard now refuses an invoke when:
- there's no Origin, or it's `null`;
- the Origin isn't one of the app's: `tauri://localhost`, `http(s)://tauri.localhost`, or the loopback dev server
  (`http://localhost|127.0.0.1|[::1]:<port>`, the `devUrl`);
- there's no Referer, or it's empty. The app's document always sends one: every app call in both G-SM14 runs carried
  Referer `tauri://localhost` (23 of 23 `ipc-protocol` lines in the rerun, `load_vault` in the first run);
- the Referer isn't a URL, is a `blob:`/`data:`/`about:`/`filesystem:`/`javascript:` URL, or isn't on the request's
  Origin;
- the Referer is a script asset or another HTML page (as before).

The app's documents still pass (`/`, `/index.html`, extension-less routes, on every app origin and the dev origin).

**Not fixable here, and rejected as a change:** Fetch lets a same-origin context name any same-origin URL as its
referrer, so a context could present `tauri://localhost/` and look like the document. No header-based check can tell
these apart, and the review agrees referrer checks can't establish frame identity. It suggests a document-only
authenticated channel instead. Tauri already provides one, and it runs before this guard:
- **The invoke key.** Tauri 2.11.2 injects its IPC script, which holds `__TAURI_INVOKE_KEY__` as a `const` in a
  closure, with `for_main_frame_only: true` (`manager/webview.rs`, `main_frame_script`). It sends the key as the
  `Tauri-Invoke-Key` header on every invoke. `Webview::on_message` drops any request whose key doesn't match, before
  the app's invoke handler (where this guard sits) is reached.
- **What G-SM14 measured.** No Worker or frame has the key: `__TAURI_INTERNALS__` and the key were absent in the
  sketch Worker, its nested Worker, the compartment frame and the frame's blob Workers. Every keyless or wrong-key
  invoke from a Worker was refused at `on_message` (11 refusals in the first run).

So the review's scenario, "an otherwise valid invoke from an app-origin URL Worker", needs a Worker that holds the
invoke key. Only the app's document can hand it over, and only by capturing it from its own `fetch`, which means
the document is already compromised. A compromised document can run the command itself. A second, LearnLoop-made
token would sit in the same place, be stealable the same way, and add nothing; under the proportionate protection bar
(owner, 2026-10-24) it isn't built. The gap is written down where it lives: in the module comment, the function
comment, the `main.rs` wrapper comment, and a Rust test that pins `(tauri://localhost, tauri://localhost/)` as
indistinguishable at this layer.

**Claims corrected.** The stage record (`reader-rw5d-p2-sketch-compartment.md` §2) said Origin and Referer "can't be
forged from a page". It now says page script can't set them as headers, but Fetch lets a context omit the Referer or
replace it with a same-origin URL. It also lists what the guard now refuses and names the invoke key as the document's
authentication. The `refusal_reason` comment and the `main.rs` wrapper comment no longer say every frame/Worker invoke
is refused. The rest of the spec-conformance table (compartment, CSP, narrow protocols, kill switch, default-on after
the recorded PASS, no DB/replay/evidence changes) needed no change.

## Gate (this fix step; the full suite runs once, in the landing gate)

Every cargo and pytest command ran in `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, one
at a time. TMPDIR was outside the worktree.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: clean.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- **Rust:** `cargo test --offline` in `apps/learnloop-tauri/src-tauri`: **31 passed, 0 failed** (29 before, plus the
  2 new `frame_guard` tests; the reproduction run before the fix: 4 passed, 1 failed on the omitted-Referer case).
  `cargo check --offline --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: clean. `rustfmt --check` on
  `frame_guard.rs`: clean. The crate as a whole isn't rustfmt-clean (that predates this stage) and was left alone.
- **Targeted pytest** (`uv run pytest -n 6`): `tests/test_desktop_rpc_contract.py` (parses `main.rs`'s
  `generate_handler!` and its wrapper), `tests/test_codex_lockdown_round3.py` (scans `src-tauri/src/*.rs`),
  `tests/test_desktop_activation_audit.py`, `tests/test_architecture.py`: **42 passed**.
- **Desktop catalog:** `desktop_generate.py` regenerated the `frame_guard` and `main` Rust notes (their sources
  changed). `desktop_validate.py` passes: 300/300 TypeScript/TSX + 6/6 Rust modules, ACTIVE=306, reproducible
  byte-for-byte.
- **Not run, and why:**
  - frontend (npm, vitest, frontend build): no frontend file changed;
  - durability lane and DB reference scripts: no migration, DB or schema change;
  - full suite: owner rule, landing gate only.

## Orchestrator scoped verify remainder, fixed

Scoped verify: Codex (gpt-6.1-sol), job `20261101-153827-RFAdme`, on `b7530c0435`. It closed F1's omitted-Referer and
unexpected-origin parts, found no false refusal on the normal Linux path, and found the guard's scope stated honestly.
One conditional regression remained:

> [P2] Legitimate Windows/macOS fallback invokes are rejected — frame_guard.rs:68. Tauri 2.11.2 switches to
> window.ipc.postMessage when custom-protocol fetch fails; on that authenticated fallback Rust builds invoke headers
> from options.headers, and LearnLoop's invoke(command, args) supplies none, so the guard rejects legitimate
> top-document calls. The fallback stays registered on Windows/macOS (Linux unregisters it). Fix: make enforcement
> transport-aware, or scope this header filter to Linux pending equivalent non-Linux handling; add a fallback
> regression check.

**Confirmed in the source.** Tauri 2.11.2 `ipc/protocol.rs` (`handle_ipc_message`) builds the fallback's
`InvokeRequest.headers` from the message's `options.headers` alone, so the app's own fallback call reaches the
guard with an empty header map, and the guard refused "no Origin".

**Fixed (`frame_guard.rs`, `main.rs`).** The header rules now take a `Platform`:
- `Platform::Linux` (the build's `PLATFORM` when `cfg!(target_os = "linux")`): unchanged. Linux unregisters the
  script-message fallback, so every app invoke comes over the custom protocol with both headers; a missing Origin or
  Referer is refused.
- `Platform::FallbackRegistered` (Windows, macOS): an absent or empty Origin or Referer is never a reason. A header
  that is present is still checked: an explicit Origin `null`, an Origin that isn't the app's, a Referer that isn't a
  URL, is a `blob:`/`data:`/`about:`/`filesystem:`/`javascript:` URL, names a script asset or another HTML page (the
  sketch frame), isn't on an app origin, or disagrees with the Origin, and a header that isn't text, are refused. On
  the fallback those headers are whatever the message names, so this is a filter, not authentication; the invoke key
  remains the document's authentication (R1).
- The functions take the platform as a parameter (`refusal_on`, `refusal_reason_on`), so both branches run in the
  Linux test build. The wrapper in `main.rs` also prints one stderr line per refusal
  (`frame_guard: refused command=… reason=…`), so a refused app call is visible in a log.

**Tests (Rust):** `linux_refuses_absent_headers`; `with_the_fallback_registered_absent_headers_pass` (including the
fallback's request as Tauri builds it, an empty header map); `with_the_fallback_registered_an_explicit_frame_or_foreign_origin_is_refused`;
`this_build_uses_its_platforms_rules` (the build's `PLATFORM` follows `target_os`). The earlier tests now name
`Platform::Linux`.

**Gate (this step):** `cargo test --offline`: **35 passed, 0 failed** (31 before, plus 4); `cargo check --offline`:
clean, no warnings; `rustfmt --check` on `frame_guard.rs`: clean. Targeted pytest (`test_desktop_rpc_contract.py`,
`test_codex_lockdown_round3.py`, `test_desktop_activation_audit.py`, `test_architecture.py`): **42 passed**.
`desktop_generate.py` regenerated the `frame_guard` and `main` notes; `desktop_validate.py` passes.
