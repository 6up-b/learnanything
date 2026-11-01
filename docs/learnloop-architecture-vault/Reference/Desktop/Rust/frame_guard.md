---
title: "Desktop module · src-tauri/src/frame_guard.rs"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src-tauri.src.frame_guard"
language: "Rust"
area: "Rust"
source_path: "apps/learnloop-tauri/src-tauri/src/frame_guard.rs"
source_paths:
  - "apps/learnloop-tauri/src-tauri/src/frame_guard.rs"
source_commit: "f76a8de7a6ccd870165fbdbded03dc74757b8a18"
source_commit_timestamp: "2026-11-01T15:36:35-05:00"
source_worktree_state: "staged-or-mixed"
activation_kind: "native-entry-reachable"
activation_evidence: "A Rust mod/use edge reaches this crate module from src-tauri/src/main.rs."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/rust"
  - "refactor/active"
---

# `src-tauri/src/frame_guard.rs`

Area: [[Reference/Desktop/Rust/_area|Rust]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `Platform`, `PLATFORM`, `refusal_on`, `refusal_reason` and related exports within the desktop's Rust ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src-tauri/src/frame_guard.rs](../../../../../apps/learnloop-tauri/src-tauri/src/frame_guard.rs) |
| Source lines | 437 |
| Language | `Rust` |
| Area | [[Reference/Desktop/Rust/_area|Rust]] |
| Refactor status | `ACTIVE` |
| Activation kind | `native-entry-reachable` |
| Worktree state | `staged-or-mixed` |
| Source commit | `f76a8de7a6ccd870165fbdbded03dc74757b8a18` |
| Commit timestamp | `2026-11-01T15:36:35-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A Rust mod/use edge reaches this crate module from src-tauri/src/main.rs.
>
> Build/entry chain: [[Reference/Desktop/Rust/main|src-tauri/src/main.rs]] → [[Reference/Desktop/Rust/frame_guard|src-tauri/src/frame_guard.rs]]

## Public API

- `pub enum Platform` — enum, line 73
- `pub const PLATFORM: Platform = if cfg!(target_os = "linux")` — const, line 84
- `pub fn refusal_on( platform: Platform, origin: Option<&str>, referer: Option<&str>, ) -> Option<&'static str>` — fn, line 102
- `pub fn refusal_reason(headers: &HeaderMap) -> Option<&'static str>` — fn, line 168
- `pub fn refusal_reason_on(platform: Platform, headers: &HeaderMap) -> Option<&'static str>` — fn, line 173

## Internal implementation anchors

- `fn app_origin(url: &Url) -> Option<String>` — fn, line 49
- `fn header<'a>(headers: &'a HeaderMap, name: &str) -> Option<&'a str>` — fn, line 159
- `fn the_apps_own_document_passes()` — fn, line 194
- `fn frames_and_workers_are_refused()` — fn, line 232
- `fn omitted_headers_and_unexpected_origins_are_refused()` — fn, line 266
- `fn a_replaced_same_origin_referrer_is_not_this_layers_to_catch()` — fn, line 299
- `fn reads_the_request_headers()` — fn, line 320
- `fn linux_refuses_absent_headers()` — fn, line 338
- `fn with_the_fallback_registered_absent_headers_pass()` — fn, line 356
- `fn with_the_fallback_registered_an_explicit_frame_or_foreign_origin_is_refused()` — fn, line 388
- `fn this_build_uses_its_platforms_rules()` — fn, line 430

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/Rust/main|src-tauri/src/main.rs]] — module declaration: module declaration; no named call claim

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `tauri`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src-tauri/src/frame_guard.rs](../../../../../apps/learnloop-tauri/src-tauri/src/frame_guard.rs) — inline Rust unit-test module; run with `cargo test` from `apps/learnloop-tauri/src-tauri`.

## Modification guidance

- Keep native code an adapter: process/protocol/window/filesystem concerns belong here, while learning rules and durable state interpretation stay in Python domains.
- Command changes must remain synchronized with `src/api/client.ts`, `src/api/dto.ts`, `main.rs` registration, and the Python sidecar registry.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src-tauri/src/frame_guard.rs](../../../../../apps/learnloop-tauri/src-tauri/src/frame_guard.rs) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
