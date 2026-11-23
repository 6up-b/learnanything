---
title: "Desktop area · TypeScript/fixtures/desks"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/fixtures/desks"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/fixtures/desks

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/fixtures/desks](../../../../../../../apps/learnloop-tauri/src/fixtures/desks)

## Responsibility

The Reader workbench's synthetic workspace (project-authored sources, desks, an in-memory desk server) and its visual harness page (test support, outside the Vite build).

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/fixtures/desks/companion|companion.ts]] | `ACTIVE` | Exposes deterministic `companion` fixture data for a reproducible desktop scenario. | 3 | 1 |
| [[Reference/Desktop/TypeScript/fixtures/desks/fakeCore|fakeCore.ts]] | `ACTIVE` | Exposes deterministic `fakeCore` fixture data for a reproducible desktop scenario. | 5 | 0 |
| [[Reference/Desktop/TypeScript/fixtures/desks/harness|harness.tsx]] | `ACTIVE` | Exposes deterministic `harness` fixture data for a reproducible desktop scenario. | 10 | 0 |
| [[Reference/Desktop/TypeScript/fixtures/desks/pads|pads.ts]] | `ACTIVE` | Exposes deterministic `pads` fixture data for a reproducible desktop scenario. | 2 | 4 |
| [[Reference/Desktop/TypeScript/fixtures/desks/sources|sources.ts]] | `ACTIVE` | Exposes deterministic `sources` fixture data for a reproducible desktop scenario. | 1 | 5 |
| [[Reference/Desktop/TypeScript/fixtures/desks/workspace|workspace.ts]] | `ACTIVE` | Exposes deterministic `workspace` fixture data for a reproducible desktop scenario. | 5 | 2 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
