---
title: "Desktop area · TypeScript/render"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/render"
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
| [[Reference/Desktop/TypeScript/render/LiveMarkdownEditor|LiveMarkdownEditor.tsx]] | `ACTIVE` | Adapts `LiveMarkdownEditor` content editing or rendering into React presentation behavior. | 2 | 1 |
| [[Reference/Desktop/TypeScript/render/MarkdownMath|MarkdownMath.tsx]] | `ACTIVE` | Adapts `MarkdownMath` content editing or rendering into React presentation behavior. | 0 | 15 |
| [[Reference/Desktop/TypeScript/render/MathLiveEditor|MathLiveEditor.tsx]] | `ACTIVE` | Adapts `MathLiveEditor` content editing or rendering into React presentation behavior. | 0 | 2 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
