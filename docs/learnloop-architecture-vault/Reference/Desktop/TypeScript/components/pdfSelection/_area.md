---
title: "Desktop area · TypeScript/components/pdfSelection"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/components/pdfSelection"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/components/pdfSelection

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/components/pdfSelection](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection)

## Responsibility

The PDF text-layer selection model: tokens, geometry, highlights, and the selection layer over a rendered page.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

- [[Reference/Desktop/TypeScript/components/pdfSelection/testing/_area|TypeScript/components/pdfSelection/testing]] — Synthetic PDFs and books built in memory for the PDF selection vitest files (test support, outside the Vite build).

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/components/pdfSelection/PdfSelectionLayer|PdfSelectionLayer.tsx]] | `ACTIVE` | Provides the reusable `PdfSelectionLayer` interaction surface used by one or more desktop workflows. | 3 | 1 |
| [[Reference/Desktop/TypeScript/components/pdfSelection/geometry|geometry.ts]] | `ACTIVE` | Provides shared `geometry` state or utility behavior for desktop components. | 1 | 2 |
| [[Reference/Desktop/TypeScript/components/pdfSelection/highlights|highlights.ts]] | `ACTIVE` | Provides shared `highlights` state or utility behavior for desktop components. | 2 | 3 |
| [[Reference/Desktop/TypeScript/components/pdfSelection/model|model.ts]] | `ACTIVE` | Provides shared `model` state or utility behavior for desktop components. | 3 | 5 |
| [[Reference/Desktop/TypeScript/components/pdfSelection/tokens|tokens.ts]] | `ACTIVE` | Provides shared `tokens` state or utility behavior for desktop components. | 0 | 2 |
| [[Reference/Desktop/TypeScript/components/pdfSelection/usePdfSelection|usePdfSelection.ts]] | `ACTIVE` | Provides shared `usePdfSelection` state or utility behavior for desktop components. | 2 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
