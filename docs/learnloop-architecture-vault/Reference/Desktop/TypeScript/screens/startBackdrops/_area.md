---
title: "Desktop area · TypeScript/screens/startBackdrops"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/startBackdrops"
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

# TypeScript/screens/startBackdrops

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/startBackdrops](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops)

## Responsibility

Canvas/SVG simulations and workers used as the start-screen visual backdrop.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/startBackdrops/CliffordBackdrop|CliffordBackdrop.tsx]] | `ACTIVE` | Implements the `CliffordBackdrop` start-screen visualization or its rendering support. | 1 | 1 |
| [[Reference/Desktop/TypeScript/screens/startBackdrops/JuliaBackdrop|JuliaBackdrop.tsx]] | `ACTIVE` | Implements the `JuliaBackdrop` start-screen visualization or its rendering support. | 3 | 1 |
| [[Reference/Desktop/TypeScript/screens/startBackdrops/LifeBackdrop|LifeBackdrop.tsx]] | `ACTIVE` | Implements the `LifeBackdrop` start-screen visualization or its rendering support. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/startBackdrops/PendulumBackdrop|PendulumBackdrop.tsx]] | `ACTIVE` | Implements the `PendulumBackdrop` start-screen visualization or its rendering support. | 1 | 1 |
| [[Reference/Desktop/TypeScript/screens/startBackdrops/ThreeBodyBackdrop|ThreeBodyBackdrop.tsx]] | `ACTIVE` | Implements the `ThreeBodyBackdrop` start-screen visualization or its rendering support. | 1 | 1 |
| [[Reference/Desktop/TypeScript/screens/startBackdrops/glyphAtlas|glyphAtlas.ts]] | `ACTIVE` | Implements the `glyphAtlas` start-screen visualization or its rendering support. | 2 | 3 |
| [[Reference/Desktop/TypeScript/screens/startBackdrops/julia.worker|julia.worker.ts]] | `ACTIVE` | Implements the `julia.worker` start-screen visualization or its rendering support. | 0 | 1 |
| [[Reference/Desktop/TypeScript/screens/startBackdrops/shared|shared.ts]] | `ACTIVE` | Implements the `shared` start-screen visualization or its rendering support. | 0 | 7 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
