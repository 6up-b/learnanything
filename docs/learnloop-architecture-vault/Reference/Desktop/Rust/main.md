---
title: "Desktop module · src-tauri/src/main.rs"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src-tauri.src.main"
language: "Rust"
area: "Rust"
source_path: "apps/learnloop-tauri/src-tauri/src/main.rs"
source_paths:
  - "apps/learnloop-tauri/src-tauri/src/main.rs"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "clean"
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

# `src-tauri/src/main.rs`

Area: [[Reference/Desktop/Rust/_area|Rust]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Bootstraps the native Tauri runtime, registers protocols and commands, and composes the sidecar and vault watcher.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src-tauri/src/main.rs](../../../../../apps/learnloop-tauri/src-tauri/src/main.rs) |
| Source lines | 569 |
| Language | `Rust` |
| Area | [[Reference/Desktop/Rust/_area|Rust]] |
| Refactor status | `ACTIVE` |
| Activation kind | `native-entry-reachable` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A Rust mod/use edge reaches this crate module from src-tauri/src/main.rs.
>
> Build/entry chain: [[Reference/Desktop/Rust/main|src-tauri/src/main.rs]]

## Public API

No library export; `fn main` is the Cargo binary entry point.

## Internal implementation anchors

- `const DEBUG_ZOOM_ENV: &str = "LEARNLOOP_TAURI_DEBUG_ZOOM"` — const, line 12
- `fn llpdf_response(status: u16, body: Vec<u8>) -> tauri::http::Response<Cow<'static, [u8]>>` — fn, line 19
- `fn serve_llpdf( manager: &SidecarManager, uri_path: &str, ) -> tauri::http::Response<Cow<'static, [u8]>>` — fn, line 28
- `fn llmedia_response( status: u16, body: Vec<u8>, extra: Option<(String, String)>, ) -> tauri::http::Response<Cow<'static, [u8]>>` — fn, line 54
- `fn slice_range(len: u64, range_header: Option<&str>) -> Option<Result<(u64, u64), ()>>` — fn, line 75
- `fn serve_llmedia( manager: &SidecarManager, uri_path: &str, range_header: Option<&str>, ) -> tauri::http::Response<Cow<'static, [u8]>>` — fn, line 103
- `fn debug_zoom_enabled() -> bool` — fn, line 147
- `fn main()` — fn, line 156
- `fn llpdf_rejects_non_content_addressed_names()` — fn, line 506
- `fn llpdf_404s_for_absent_store_file()` — fn, line 521
- `fn llmedia_rejects_non_content_addressed_names()` — fn, line 527
- `fn llmedia_404s_for_absent_animation()` — fn, line 544
- `fn slice_range_math()` — fn, line 553

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [apps/learnloop-tauri/src-tauri/Cargo.toml](../../../../../apps/learnloop-tauri/src-tauri/Cargo.toml) — Cargo binary entry point.

## Dependencies

### Desktop source modules

- [[Reference/Desktop/Rust/commands|src-tauri/src/commands.rs]] — module declaration
- [[Reference/Desktop/Rust/errors|src-tauri/src/errors.rs]] — module declaration
- [[Reference/Desktop/Rust/sidecar|src-tauri/src/sidecar.rs]] — module declaration
- [[Reference/Desktop/Rust/vault_watcher|src-tauri/src/vault_watcher.rs]] — module declaration

### Assets, platform, and third-party dependencies

- Rust standard library: `std`
- Imported packages/crates: `tauri`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Architecture Overview#Runtime composition|runtime composition]] — shows this entry point in the whole process graph.
- [[Workflows/Initialize a Vault|Initialize a Vault]] — owns first-run behavior.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src-tauri/src/main.rs](../../../../../apps/learnloop-tauri/src-tauri/src/main.rs) — inline Rust unit-test module; run with `cargo test` from `apps/learnloop-tauri/src-tauri`.
- [tests/test_desktop_rpc_contract.py](../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Keep native code an adapter: process/protocol/window/filesystem concerns belong here, while learning rules and durable state interpretation stay in Python domains.
- Command changes must remain synchronized with `src/api/client.ts`, `src/api/dto.ts`, `main.rs` registration, and the Python sidecar registry.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src-tauri/src/main.rs](../../../../../apps/learnloop-tauri/src-tauri/src/main.rs) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
