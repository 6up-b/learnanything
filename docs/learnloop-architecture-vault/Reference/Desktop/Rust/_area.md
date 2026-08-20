---
title: "Desktop area · Rust"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src-tauri/src"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# Rust

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src-tauri/src](../../../../../apps/learnloop-tauri/src-tauri/src)

## Responsibility

The native Tauri shell, command bridge, sidecar process manager, error contract, and vault watcher.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/Rust/commands|commands.rs]] | `ACTIVE` | Implements the native command boundary, adapting Tauri invocations to typed JSON-RPC calls on the Python sidecar. | 3 | 1 |
| [[Reference/Desktop/Rust/errors|errors.rs]] | `ACTIVE` | Defines the serializable native command error contract and distinguishes retryable application failures from invalidated transports. | 0 | 3 |
| [[Reference/Desktop/Rust/main|main.rs]] | `ACTIVE` | Bootstraps the native Tauri runtime, registers protocols and commands, and composes the sidecar and vault watcher. | 4 | 0 |
| [[Reference/Desktop/Rust/sidecar|sidecar.rs]] | `ACTIVE` | Owns the Python sidecar child process, vault selection, JSON-RPC request lifecycle, timeout, restart, and isolated long-running calls. | 1 | 3 |
| [[Reference/Desktop/Rust/vault_watcher|vault_watcher.rs]] | `ACTIVE` | Coalesces native filesystem mutations and asks the Python authority to refresh the selected vault before notifying the renderer. | 1 | 2 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
