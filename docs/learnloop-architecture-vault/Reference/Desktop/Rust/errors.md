---
title: "Desktop module · src-tauri/src/errors.rs"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src-tauri.src.errors"
language: "Rust"
area: "Rust"
source_path: "apps/learnloop-tauri/src-tauri/src/errors.rs"
source_paths:
  - "apps/learnloop-tauri/src-tauri/src/errors.rs"
source_commit: "c308660e82bfb461f8b7d295f89d797613e32aff"
source_commit_timestamp: "2026-09-23T12:09:28-04:00"
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

# `src-tauri/src/errors.rs`

Area: [[Reference/Desktop/Rust/_area|Rust]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Defines the serializable native command error contract and distinguishes retryable application failures from invalidated transports.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src-tauri/src/errors.rs](../../../../../apps/learnloop-tauri/src-tauri/src/errors.rs) |
| Source lines | 204 |
| Language | `Rust` |
| Area | [[Reference/Desktop/Rust/_area|Rust]] |
| Refactor status | `ACTIVE` |
| Activation kind | `native-entry-reachable` |
| Worktree state | `clean` |
| Source commit | `c308660e82bfb461f8b7d295f89d797613e32aff` |
| Commit timestamp | `2026-09-23T12:09:28-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A Rust mod/use edge reaches this crate module from src-tauri/src/main.rs.
>
> Build/entry chain: [[Reference/Desktop/Rust/main|src-tauri/src/main.rs]] → [[Reference/Desktop/Rust/errors|src-tauri/src/errors.rs]]

## Public API

- `pub const SIDECAR_TIMEOUT_CODE: &str = "sidecar_timeout"` — const, line 4
- `pub const SIDECAR_UNAVAILABLE_CODE: &str = "sidecar_unavailable"` — const, line 5
- `pub const SIDECAR_PROTOCOL_CODE: &str = "sidecar_protocol_error"` — const, line 6
- `pub const VAULT_CHANGED_CODE: &str = "vault_changed"` — const, line 7
- `pub const GRADING_PROVIDER_RESET_CODE: &str = "grading_provider_reset"` — const, line 8
- `pub struct CommandError` — struct, line 12
- `pub fn task_failed(diagnostic: impl Into<String>) -> Self` — fn, line 20
- `pub fn state_unavailable() -> Self` — fn, line 31
- `pub fn unavailable(details: Value) -> Self` — fn, line 42
- `pub fn outcome_unknown(mut details: Value) -> Self` — fn, line 52
- `pub fn protocol(mut details: Value) -> Self` — fn, line 67
- `pub fn timeout(details: Value) -> Self` — fn, line 82
- `pub fn vault_changed(message: &str, details: Value) -> Self` — fn, line 94
- `pub fn grading_provider_reset(provider: &str, cause: CommandError) -> Self` — fn, line 106
- `pub fn from_rpc(error: &Value) -> Self` — fn, line 121
- `pub fn invalidates_sidecar(&self) -> bool` — fn, line 148

## Internal implementation anchors

- `fn malformed_rpc_errors_are_protocol_failures()` — fn, line 161
- `fn application_errors_preserve_the_typed_contract()` — fn, line 169
- `fn unknown_commit_failures_are_not_safe_to_retry()` — fn, line 187

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/Rust/commands|src-tauri/src/commands.rs]] — crate import: `errors`; references `errors`
- [[Reference/Desktop/Rust/main|src-tauri/src/main.rs]] — module declaration: module declaration; no named call claim
- [[Reference/Desktop/Rust/sidecar|src-tauri/src/sidecar.rs]] — crate import: `errors`; references `errors`
- [[Reference/Desktop/Rust/vault_watcher|src-tauri/src/vault_watcher.rs]] — crate import: `errors`; references `errors`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `serde`, `serde_json`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src-tauri/src/errors.rs](../../../../../apps/learnloop-tauri/src-tauri/src/errors.rs) — inline Rust unit-test module; run with `cargo test` from `apps/learnloop-tauri/src-tauri`.
- [tests/test_desktop_rpc_contract.py](../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Keep native code an adapter: process/protocol/window/filesystem concerns belong here, while learning rules and durable state interpretation stay in Python domains.
- Command changes must remain synchronized with `src/api/client.ts`, `src/api/dto.ts`, `main.rs` registration, and the Python sidecar registry.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src-tauri/src/errors.rs](../../../../../apps/learnloop-tauri/src-tauri/src/errors.rs) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
