---
title: "Desktop module · src-tauri/src/sidecar.rs"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src-tauri.src.sidecar"
language: "Rust"
area: "Rust"
source_path: "apps/learnloop-tauri/src-tauri/src/sidecar.rs"
source_paths:
  - "apps/learnloop-tauri/src-tauri/src/sidecar.rs"
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

# `src-tauri/src/sidecar.rs`

Area: [[Reference/Desktop/Rust/_area|Rust]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Owns the Python sidecar child process, vault selection, JSON-RPC request lifecycle, timeout, restart, and isolated long-running calls.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src-tauri/src/sidecar.rs](../../../../../apps/learnloop-tauri/src-tauri/src/sidecar.rs) |
| Source lines | 591 |
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
> Build/entry chain: [[Reference/Desktop/Rust/main|src-tauri/src/main.rs]] → [[Reference/Desktop/Rust/sidecar|src-tauri/src/sidecar.rs]]

## Public API

- `pub struct SidecarManager` — struct, line 42
- `pub fn new() -> Self` — fn, line 68
- `pub fn initialize(&self, vault_path: Option<String>) -> Result<Value, CommandError>` — fn, line 77
- `pub fn resolved_vault_path(&self) -> PathBuf` — fn, line 115
- `pub fn select_vault(&self, vault_path: Option<String>) -> Result<Value, CommandError>` — fn, line 124
- `pub fn call(&self, method: &str, params: Value) -> Result<Value, CommandError>` — fn, line 133
- `pub fn call_isolated(&self, method: &str, params: Value) -> Result<Value, CommandError>` — fn, line 171

## Internal implementation anchors

- `const DEFAULT_RESPONSE_TIMEOUT_SECS: u64 = 16 * 60` — const, line 14
- `const DEFAULT_STARTUP_TIMEOUT_SECS: u64 = 15` — const, line 15
- `const SHUTDOWN_TIMEOUT_SECS: u64 = 2` — const, line 16
- `fn response_timeout() -> Duration` — fn, line 18
- `fn startup_timeout() -> Duration` — fn, line 25
- `fn timeout_from_env(name: &str, default_secs: u64) -> Duration` — fn, line 32
- `struct SidecarState` — struct, line 46
- `struct SidecarClient` — struct, line 51
- `struct SidecarCommandSpec` — struct, line 61
- `fn stop_client(client: &mut SidecarClient, graceful: bool)` — fn, line 190
- `fn spawn() -> Result<Self, CommandError>` — fn, line 205
- `fn launch(repo_root: &Path, spec: SidecarCommandSpec) -> Result<Self, String>` — fn, line 238
- `fn call(&mut self, method: &str, params: Value) -> Result<Value, CommandError>` — fn, line 278
- `fn call_with_timeout( &mut self, method: &str, params: Value, timeout: Duration, ) -> Result<Value, CommandError>` — fn, line 282
- `fn terminate(&mut self)` — fn, line 344
- `fn drop(&mut self)` — fn, line 351
- `fn parse_response( line: &str, expected_id: u64, method: &str, launcher: &str, ) -> Result<Value, CommandError>` — fn, line 356
- `fn spawn_reader(stdout: ChildStdout) -> Receiver<std::io::Result<String>>` — fn, line 390
- `fn sidecar_command_specs(repo_root: &Path) -> Vec<SidecarCommandSpec>` — fn, line 413
- `fn python_spec(program: OsString, label: &str) -> SidecarCommandSpec` — fn, line 455
- `fn uv_spec() -> SidecarCommandSpec` — fn, line 463
- `fn venv_python(repo_root: &Path) -> Option<PathBuf>` — fn, line 476
- `fn active_env_python() -> Option<PathBuf>` — fn, line 489
- `fn repo_root() -> PathBuf` — fn, line 510
- `fn default_vault_path() -> PathBuf` — fn, line 517
- `fn resolve_vault_path(requested: Option<PathBuf>, selected: Option<PathBuf>) -> PathBuf` — fn, line 528
- `fn python_path(repo_root: &Path) -> String` — fn, line 535
- `fn reconnect_keeps_the_selected_vault()` — fn, line 552
- `fn response_parser_requires_a_complete_matching_envelope()` — fn, line 566

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/Rust/commands|src-tauri/src/commands.rs]] — crate import: `sidecar`; references `sidecar`
- [[Reference/Desktop/Rust/main|src-tauri/src/main.rs]] — module declaration: module declaration; no named call claim
- [[Reference/Desktop/Rust/vault_watcher|src-tauri/src/vault_watcher.rs]] — crate import: `sidecar`; references `sidecar`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/Rust/errors|src-tauri/src/errors.rs]] — crate import; imports `errors`

### Assets, platform, and third-party dependencies

- Rust standard library: `std`
- Imported packages/crates: `serde_json`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src-tauri/src/sidecar.rs](../../../../../apps/learnloop-tauri/src-tauri/src/sidecar.rs) — inline Rust unit-test module; run with `cargo test` from `apps/learnloop-tauri/src-tauri`.
- [tests/test_desktop_rpc_contract.py](../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Keep native code an adapter: process/protocol/window/filesystem concerns belong here, while learning rules and durable state interpretation stay in Python domains.
- Command changes must remain synchronized with `src/api/client.ts`, `src/api/dto.ts`, `main.rs` registration, and the Python sidecar registry.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src-tauri/src/sidecar.rs](../../../../../apps/learnloop-tauri/src-tauri/src/sidecar.rs) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
