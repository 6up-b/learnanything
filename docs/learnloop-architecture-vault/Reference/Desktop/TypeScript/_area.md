---
title: "Desktop area · TypeScript"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src"
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

# TypeScript

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src](../../../../../apps/learnloop-tauri/src)

## Responsibility

The React renderer entry point and cross-cutting frontend modules.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

- [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] — Typed DTOs and the renderer-to-Tauri invocation facade.
- [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] — Desktop shell orchestration, keyboard policy, configuration helpers, and recent-vault state.
- [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] — Reusable learner-facing controls and composite interaction surfaces.
- [[Reference/Desktop/TypeScript/fixtures/_area|TypeScript/fixtures]] — Deterministic renderer fixtures used to demonstrate or restore known states.
- [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] — Markdown, mathematics, and live-editor rendering adapters.
- [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] — Top-level routed workflow screens in the desktop shell.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/errors|errors.ts]] | `ACTIVE` | Turns unknown renderer failures into the user-facing desktop error contract. | 1 | 12 |
| [[Reference/Desktop/TypeScript/main|main.tsx]] | `ACTIVE` | Bootstraps React, applies the persisted palette before first paint, and mounts the desktop application shell. | 1 | 0 |
| [[Reference/Desktop/TypeScript/queueEvents|queueEvents.ts]] | `ACTIVE` | Provides the in-window event boundary that tells independent surfaces the practice queue changed. | 0 | 5 |
| [[Reference/Desktop/TypeScript/vite-env.d|vite-env.d.ts]] | `ACTIVE` | Adds Vite's ambient client declarations to the TypeScript compilation unit. | 0 | 0 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
