---
title: "Desktop area · TypeScript/render"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/render"
source_commit: "76b7e44272ab57e22c23c1d73d6d916535f4a857"
source_commit_timestamp: "2026-11-03T12:15:55-05:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/render

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/render](../../../../../../apps/learnloop-tauri/src/render)

## Responsibility

Markdown, mathematics, and live-editor rendering adapters.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/render/LiveMarkdownEditor|LiveMarkdownEditor.tsx]] | `ACTIVE` | Adapts `LiveMarkdownEditor` content editing or rendering into React presentation behavior. | 2 | 2 |
| [[Reference/Desktop/TypeScript/render/MarkdownMath|MarkdownMath.tsx]] | `ACTIVE` | Adapts `MarkdownMath` content editing or rendering into React presentation behavior. | 1 | 35 |
| [[Reference/Desktop/TypeScript/render/MathLiveEditor|MathLiveEditor.tsx]] | `ACTIVE` | Adapts `MathLiveEditor` content editing or rendering into React presentation behavior. | 0 | 2 |
| [[Reference/Desktop/TypeScript/render/markdownPipeline|markdownPipeline.ts]] | `ACTIVE` | Adapts `markdownPipeline` content editing or rendering into React presentation behavior. | 0 | 2 |
| [[Reference/Desktop/TypeScript/render/pageMathSegments|pageMathSegments.ts]] | `ACTIVE` | Adapts `pageMathSegments` content editing or rendering into React presentation behavior. | 1 | 0 |
| [[Reference/Desktop/TypeScript/render/readerBlockPolicy|readerBlockPolicy.ts]] | `ACTIVE` | Adapts `readerBlockPolicy` content editing or rendering into React presentation behavior. | 1 | 2 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
