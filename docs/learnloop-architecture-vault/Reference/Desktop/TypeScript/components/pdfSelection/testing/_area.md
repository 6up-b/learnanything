---
title: "Desktop area · TypeScript/components/pdfSelection/testing"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/components/pdfSelection/testing"
source_commit: "e2916ff0e7ba40841036aa11af2f95256708db50"
source_commit_timestamp: "2026-10-15T20:38:52-04:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/components/pdfSelection/testing

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/components/pdfSelection/testing](../../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/testing)

## Responsibility

Synthetic PDFs and books built in memory for the PDF selection vitest files (test support, outside the Vite build).

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/components/pdfSelection/testing/syntheticBook|syntheticBook.ts]] | `ACTIVE` | Provides shared `syntheticBook` state or utility behavior for desktop components. | 2 | 0 |
| [[Reference/Desktop/TypeScript/components/pdfSelection/testing/syntheticPdf|syntheticPdf.ts]] | `ACTIVE` | Provides shared `syntheticPdf` state or utility behavior for desktop components. | 0 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
