# Mobile M1: Codex review fixes

Branch `mobile/m1`. Review job: `~/.cache/codex-agent/jobs/20261012-003150-Aa4FWd`.
Base before the fixes: `9c3e431f`. Every finding was first reproduced with a failing
test, then fixed. No finding was rejected. Owner decisions applied: revision 4
of the spec (on primary `main`) for §4.6 and §4.7, D12 (no LearnLoop tailnet
policy), and frictionless defaults.

## Review

| ID | Severity | Title | Verdict | Commit | Test (failing before the fix) |
|---|---|---|---|---|---|
| F1 | High | Doctor approves an additional public forward to the backend | fixed | `19715479` | `tests/test_mobile_doctor.py::test_serve_rejects_any_second_path_to_the_backend` (11 cases: a TLS-terminated TCPForward on 8443 with and without Funnel, a second web route with Funnel, foreground sessions, Service configs, an unparseable target; two unrelated mappings still pass). 9 failed before the fix |
| F2 | Medium | Crash recovery requires form values that were never persisted | fixed | `983939c0` | `tests/test_capture_route_recovery.py::test_crash_before_destination_accepts_new_inputs_after_restart`, `::test_resume_finishes_an_unfinished_route_without_any_inputs` (before and after the destination commit), `::test_crash_before_destination_allows_choosing_another_route`, `::test_purge_erases_the_persisted_request`. All three routes (card, Quick Add, tutor). Parameters are rebuilt from scratch after a simulated crash. Frontend: `InboxStrip.test.tsx` "finishes an unfinished save after a restart…" |
| F3 | Medium | Older handled captures cannot be purged from the desktop | fixed | `4275516d` | `tests/test_capture_domain.py::test_old_handled_capture_is_reachable_past_100_newer_and_tombstones` (121+ captures with dismissed captures and purged tombstones). `InboxStrip.test.tsx` "pages past 100 newer captures and purged tombstones…" and "keeps deletion-pending captures reachable…" |
| F4 | Medium | The photo-to-card fallback never shows the photo | fixed | `51d81ec8` | `tests/test_capture_domain.py::test_photo_preview_is_resolved_from_the_stored_hash_only`, `::test_photo_preview_refuses_tampered_hashes_missing_files_and_purge`, `tests/test_capture_desktop.py::test_desktop_photo_preview_rpc_reads_only_the_capture_original`. `WriteCardDialog.photo.test.tsx` (unmocked dialog). `InboxStrip.test.tsx` "shows a photo-only capture's image…" |
| F5 | Medium | Per-device throttling interrupts ordinary outbox flushing | fixed | `3832e82f` | `tests/test_mobile_host_auth.py::test_offline_backlog_flushes_without_per_device_throttle` (45 captures and 45 receipt retries in one run). The 31st capture got 429 before the fix |
| F6 | Low | Doctor presents the rejected phone-only policy as required work | fixed | `19715479` | `tests/test_mobile_doctor.py::test_doctor_checks_fake_deployment_without_mutating_vault` now requires that no check is a policy check or `owner must confirm`, and that the recipe is labelled optional. It failed on the original doctor |
| C1 | (conformance note) | §4.7: Tailscale health warnings were not surfaced | fixed | `19715479` | Same doctor test: a `Health` entry appears as a non-fatal `warning` check and `ok` stays true |

### What changed

- **F1.** `serve_checks` walks the background config, every `Foreground` session and every `Services` config. The expected background `HTTPS :443 / → http://127.0.0.1:<port>` must be the **only** route to the backend port.
  - Any `TCPForward`, with or without `TerminateTLS`, and any other `Proxy` route to that port fails `serve`.
  - Any Funnel on `:443`, or on a port that carries such a route, fails `funnel`.
  - Targets on any host count, and unparseable targets fail closed.
  - Funnel on unrelated ports (other services) is not LearnLoop's concern and passes.
- **F2.** Route intents now persist their request, and purge still erases it. Captures expose `pending_route` while they are `new`.
  - The new desktop-only `resume_capture_route` replays the exact stored request through its own handler. This recovers a committed destination or creates a missing one, and the strip offers **Finish saving**.
  - A different request or route replaces an unfinished intent only after its destination is shown to be absent. The check uses a fresh vault load for cards, the `batch_capture_*` row for Quick Add, and the question event for tutor questions. Anything uncertain counts as committed. The replacement is a compare-and-swap on the stale destination ID.
  - A committed but incomplete tutor event is still a hard stop that avoids duplicate spend (§9.1). The fence assumes the single desktop sidecar, which handles requests serially.
- **F3.** The handled view pages with **Load older**, and polling re-reads every loaded page.
  - The inbox summary carries every deletion-pending capture (new `delete_pending` filter) with Retry delete, in both views. A failed unlink therefore can't be buried behind newer captures.
  - Purged tombstones are labelled "Purged capture"; before, purged text was shown as "Photo capture".
- **F4.** The new desktop-only `get_capture_media(capture_id)` returns a bounded preview (2048 px, JPEG or PNG for alpha) as a data URL.
  - The file is resolved only from the capture's stored hash, which must match `sha256:[0-9a-f]{64}`. The bytes must still hash to it.
  - Purged and non-photo captures are refused, so no caller-supplied or arbitrary path is read.
  - The strip offers **View photo**, and `WriteCardDialog` shows the photo above the fields for photo captures.
  - The mobile host still default-denies every sidecar method; `test_every_registry_method_is_http_denied` covers the new ones.
- **F5.** Per-device and per-token throttling is removed. Bounded admission (16 short, 2 capture, 1 media) remains. Pairing keeps its in-memory 30-per-minute budget plus the durable per-record and global locks. `docs/mobile-shortcuts.md` no longer lists 429 for captures.
- **F6.** The `effective_policy` "owner must confirm" entry is gone. The recipe is returned as `optional_policy_example` with a note saying it is optional and not needed for acceptance (D12). `docs/reviews/mobile-m1.md` setup text now defines A2 as revision 4 does.

### Codex's unverified claims

- **"Doctor verifies safe exposure."** Corrected by F1.
- **"Durable route intents provide crash recovery."** Now true without the original parameters (F2).
- **"The desktop provides an image-to-card fallback."** Now shows the image (F4).
- **Suite counts.** Reproduced below in a synced worktree environment.
- **Shortcut asks to classify text versus URL (C1–C4 row).** Not changed. It belongs to the Shortcut UX, not to a finding, and it is out of this stage's fix scope.

## Gate (2026-10-12, worktree `learnanything-mobile-m1`, HEAD after the fix commits)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **8 kept, 0 broken** |
| `uv run pytest -n auto` | **6296 passed**, 46 warnings, 0 failed (189 s) |
| `uv run pytest -m durability` | **66 passed**, 6230 deselected, 1 warning |
| `npm install` (apps/learnloop-tauri) | up to date. Same 14 audit findings as before; no forced upgrades |
| `npm run typecheck` | passed (exit 0) |
| `npm test` (vitest) | **44 passed** in 10 files |
| `npm run frontend:build` (extra) | passed. Same >500 KB chunk warning as before |
| DB reference generate/validate | not needed: no migration or schema change. `pending_route` is a computed column in a query |
| `cargo check` (extra) | not runnable: the machine's `rustc` still fails with the same `librustc_driver` symbol-lookup error recorded in `mobile-m1.md`. The Rust edits are two `sidecar_passthrough!` lines plus handler registrations. `tests/test_desktop_rpc_contract.py` checks them statically across all four layers |

The warnings are Starlette's TestClient deprecation and the existing Python 3.12 datetime-adapter and fork warnings. No live or paid AI call, Tailscale command, owner vault or `~/.config/learnloop/` was used. The tracked fixtures were not touched.
