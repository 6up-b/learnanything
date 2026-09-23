---
title: "Desktop area · TypeScript/app"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/app"
source_commit: "b0a5685663ea4ce3beff013662d6d78dd5e1a10c"
source_commit_timestamp: "2026-09-23T14:05:41-04:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/app

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/app](../../../../../../apps/learnloop-tauri/src/app)

## Responsibility

Desktop shell orchestration, keyboard policy, configuration helpers, and recent-vault state.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/app/App|App.tsx]] | `ACTIVE` | Owns desktop navigation and cross-screen state, connecting startup, sessions, overlays, vault refresh, and route handoffs. | 42 | 1 |
| [[Reference/Desktop/TypeScript/app/ScreenErrorBoundary|ScreenErrorBoundary.tsx]] | `ACTIVE` | Provides `ScreenErrorBoundary` within the desktop's TypeScript/app ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/app/algoConfig|algoConfig.ts]] | `ACTIVE` | Normalizes and exposes algorithm configuration values needed by presentation code. | 0 | 9 |
| [[Reference/Desktop/TypeScript/app/keyboard|keyboard.ts]] | `ACTIVE` | Centralizes keyboard-target and shortcut guards shared by desktop interactions. | 0 | 3 |
| [[Reference/Desktop/TypeScript/app/practiceOffer|practiceOffer.ts]] | `ACTIVE` | Provides `PracticeOffer`, `schedulerCandidateForServe` within the desktop's TypeScript/app ownership area. | 0 | 1 |
| [[Reference/Desktop/TypeScript/app/recentVaults|recentVaults.ts]] | `ACTIVE` | Persists and normalizes the renderer's recent-vault list. | 0 | 2 |
| [[Reference/Desktop/TypeScript/app/useCloseWithFlush|useCloseWithFlush.ts]] | `ACTIVE` | Provides `useCloseWithFlush` within the desktop's TypeScript/app ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/app/vaultTransition|vaultTransition.ts]] | `ACTIVE` | Provides `registerVaultDraft`, `selectWithDraftFlush` within the desktop's TypeScript/app ownership area. | 0 | 2 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
