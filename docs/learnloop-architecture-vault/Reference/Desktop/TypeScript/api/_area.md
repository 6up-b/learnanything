---
title: "Desktop area · TypeScript/api"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/api"
source_commit: "47c892762f2845348a5efaa4d16192161094013f"
source_commit_timestamp: "2026-11-02T05:28:14-05:00"
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
| [[Reference/Desktop/TypeScript/api/capture|capture.ts]] | `ACTIVE` | Provides `CaptureDto`, `InboxSummary`, `CaptureMediaDto` within the desktop's TypeScript/api ownership area. | 0 | 3 |
| [[Reference/Desktop/TypeScript/api/client|client.ts]] | `ACTIVE` | Defines the typed renderer-side RPC facade that converts UI actions into named Tauri commands. | 5 | 120 |
| [[Reference/Desktop/TypeScript/api/dto|dto.ts]] | `ACTIVE` | Owns the renderer's TypeScript representation of sidecar request, response, and view contracts. | 0 | 206 |
| [[Reference/Desktop/TypeScript/api/queryCache|queryCache.ts]] | `ACTIVE` | Provides `QueryKey`, `QueryTag`, `QueryState`, `FetchOptions` and related exports within the desktop's TypeScript/api ownership area. | 2 | 13 |
| [[Reference/Desktop/TypeScript/api/queryTags|queryTags.ts]] | `ACTIVE` | Provides `TAG`, `KnownTag`, `READER_PREFIX`, `readerTag` within the desktop's TypeScript/api ownership area. | 0 | 22 |
| [[Reference/Desktop/TypeScript/api/useCachedQuery|useCachedQuery.ts]] | `ACTIVE` | Provides `CachedQuery`, `CachedQueryOptions`, `useCachedQuery`, `useReportQueryError` within the desktop's TypeScript/api ownership area. | 3 | 17 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
