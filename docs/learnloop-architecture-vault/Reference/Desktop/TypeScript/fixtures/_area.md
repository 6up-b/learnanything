---
title: "Desktop area · TypeScript/fixtures"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/fixtures"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/fixtures

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/fixtures](../../../../../../apps/learnloop-tauri/src/fixtures)

## Responsibility

Deterministic renderer fixtures used to demonstrate or restore known states.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/fixtures/readerIntentContract|readerIntentContract.ts]] | `ACTIVE` | Exposes deterministic `readerIntentContract` fixture data for a reproducible desktop scenario. | 1 | 0 |
| [[Reference/Desktop/TypeScript/fixtures/readerRenderView|readerRenderView.ts]] | `ACTIVE` | Exposes deterministic `readerRenderView` fixture data for a reproducible desktop scenario. | 1 | 1 |
| [[Reference/Desktop/TypeScript/fixtures/retryRequests|retryRequests.ts]] | `ACTIVE` | Exposes deterministic `retryRequests` fixture data for a reproducible desktop scenario. | 1 | 0 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
