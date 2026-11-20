---
title: "Desktop area · TypeScript/copy"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/copy"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/copy

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/copy](../../../../../../apps/learnloop-tauri/src/copy)

## Responsibility

Learner-facing copy policy: the jargon deny-list the vitest lints apply, and plain-language ingest error wording.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/copy/denyList|denyList.ts]] | `ACTIVE` | Provides `DenyTerm`, `DENY_TERMS`, `findJargon` within the desktop's TypeScript/copy ownership area. | 0 | 0 |
| [[Reference/Desktop/TypeScript/copy/ingestErrors|ingestErrors.ts]] | `ACTIVE` | Provides `PlainError`, `plainError` within the desktop's TypeScript/copy ownership area. | 1 | 4 |
| [[Reference/Desktop/TypeScript/copy/refusals|refusals.ts]] | `ACTIVE` | Provides `NO_HINTS_ON_YOUR_OWN`, `NO_HINTS_SHORT_CHECK`, `NO_ASK_SHORT_CHECK`, `NO_ASK_TEACH_BACK` and related exports within the desktop's TypeScript/copy ownership area. | 1 | 3 |
| [[Reference/Desktop/TypeScript/copy/waiting|waiting.ts]] | `ACTIVE` | Provides `WAITING_COPY` within the desktop's TypeScript/copy ownership area. | 0 | 9 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
