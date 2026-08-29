---
title: "Desktop module · src-tauri/src/vault_watcher.rs"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src-tauri.src.vault_watcher"
language: "Rust"
area: "Rust"
source_path: "apps/learnloop-tauri/src-tauri/src/vault_watcher.rs"
source_paths:
  - "apps/learnloop-tauri/src-tauri/src/vault_watcher.rs"
source_commit: "49f8dc415492edd91c09d47c911fc1530c675242"
source_commit_timestamp: "2026-07-27T02:40:21-04:00"
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

# `src-tauri/src/vault_watcher.rs`

Area: [[Reference/Desktop/Rust/_area|Rust]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Coalesces native filesystem mutations and asks the Python authority to refresh the selected vault before notifying the renderer.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src-tauri/src/vault_watcher.rs](../../../../../apps/learnloop-tauri/src-tauri/src/vault_watcher.rs) |
| Source lines | 299 |
| Language | `Rust` |
| Area | [[Reference/Desktop/Rust/_area|Rust]] |
| Refactor status | `ACTIVE` |
| Activation kind | `native-entry-reachable` |
| Worktree state | `clean` |
| Source commit | `49f8dc415492edd91c09d47c911fc1530c675242` |
| Commit timestamp | `2026-07-27T02:40:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A Rust mod/use edge reaches this crate module from src-tauri/src/main.rs.
>
> Build/entry chain: [[Reference/Desktop/Rust/main|src-tauri/src/main.rs]] → [[Reference/Desktop/Rust/vault_watcher|src-tauri/src/vault_watcher.rs]]

## Public API

- `pub const VAULT_FILES_CHANGED_EVENT: &str = "learnloop://vault-files-changed"` — const, line 11
- `pub struct VaultWatcher` — struct, line 18
- `pub fn start(app: AppHandle, sidecar: SidecarManager) -> Self` — fn, line 31
- `pub fn watch(&self, root: PathBuf)` — fn, line 37

## Internal implementation anchors

- `struct VaultFilesChanged` — struct, line 24
- `fn watch_loop(target_rx: Receiver<PathBuf>, app: AppHandle, sidecar: SidecarManager)` — fn, line 43
- `fn newest_target(target_rx: &Receiver<PathBuf>, block: bool) -> Option<PathBuf>` — fn, line 128
- `fn install_watch( root: &Path, event_tx: Sender<notify::Result<Event>>, ) -> notify::Result<RecommendedWatcher>` — fn, line 140
- `fn collect_paths(event: notify::Result<Event>, root: &Path, paths: &mut BTreeSet<PathBuf>) -> bool` — fn, line 149
- `fn is_ignored_relative_path(relative: &Path) -> bool` — fn, line 186
- `fn is_watchable_relative_path(relative: &Path) -> bool` — fn, line 200
- `fn emit_error(app: &AppHandle, root: &Path, code: &str, message: String)` — fn, line 212
- `fn path_for_wire(path: &Path) -> String` — fn, line 221
- `fn watcher_accepts_domain_files_and_excludes_runtime_artifacts()` — fn, line 234
- `fn wire_paths_are_platform_neutral()` — fn, line 249
- `fn read_access_does_not_trigger_a_refresh_loop()` — fn, line 257
- `fn a_domain_directory_mutation_forces_a_full_refresh()` — fn, line 284

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/Rust/commands|src-tauri/src/commands.rs]] — crate import: `vault_watcher`; references `vault_watcher`
- [[Reference/Desktop/Rust/main|src-tauri/src/main.rs]] — module declaration: module declaration; no named call claim

## Dependencies

### Desktop source modules

- [[Reference/Desktop/Rust/sidecar|src-tauri/src/sidecar.rs]] — crate import; imports `sidecar`

### Assets, platform, and third-party dependencies

- Rust standard library: `std`
- Imported packages/crates: `notify`, `serde`, `serde_json`, `tauri`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Inspect Persistent State|Inspect Persistent State]] — owns safe inspection.
- [[Architecture/State and Persistence#Open modes and migrations|state open modes]] — owns persistence safety.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src-tauri/src/vault_watcher.rs](../../../../../apps/learnloop-tauri/src-tauri/src/vault_watcher.rs) — inline Rust unit-test module; run with `cargo test` from `apps/learnloop-tauri/src-tauri`.
- [tests/test_desktop_rpc_contract.py](../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Keep native code an adapter: process/protocol/window/filesystem concerns belong here, while learning rules and durable state interpretation stay in Python domains.
- Command changes must remain synchronized with `src/api/client.ts`, `src/api/dto.ts`, `main.rs` registration, and the Python sidecar registry.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src-tauri/src/vault_watcher.rs](../../../../../apps/learnloop-tauri/src-tauri/src/vault_watcher.rs) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
