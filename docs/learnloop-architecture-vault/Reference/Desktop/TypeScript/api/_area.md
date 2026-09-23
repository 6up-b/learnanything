---
title: "Desktop area · TypeScript/api"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/api"
source_commit: "0395ae32f9e2e40d1cb98b38402631299a94003f"
source_commit_timestamp: "2026-09-07T12:49:13-04:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/api

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/api](../../../../../../apps/learnloop-tauri/src/api)

## Responsibility

Typed DTOs and the renderer-to-Tauri invocation facade.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/api/client|client.ts]] | `ACTIVE` | Defines the typed renderer-side RPC facade that converts UI actions into named Tauri commands. | 3 | 52 |
| [[Reference/Desktop/TypeScript/api/dto|dto.ts]] | `ACTIVE` | Owns the renderer's TypeScript representation of sidecar request, response, and view contracts. | 0 | 73 |
| [[Reference/Desktop/TypeScript/api/queryCache|queryCache.ts]] | `ACTIVE` | Provides `QueryKey`, `QueryTag`, `QueryState`, `FetchOptions` and related exports within the desktop's TypeScript/api ownership area. | 2 | 5 |
| [[Reference/Desktop/TypeScript/api/queryTags|queryTags.ts]] | `ACTIVE` | Provides `TAG`, `KnownTag`, `READER_PREFIX`, `readerTag` within the desktop's TypeScript/api ownership area. | 0 | 14 |
| [[Reference/Desktop/TypeScript/api/useCachedQuery|useCachedQuery.ts]] | `ACTIVE` | Provides `CachedQuery`, `CachedQueryOptions`, `useCachedQuery` within the desktop's TypeScript/api ownership area. | 2 | 12 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
