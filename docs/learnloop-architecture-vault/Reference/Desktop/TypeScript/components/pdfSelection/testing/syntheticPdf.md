---
title: "Desktop module · src/components/pdfSelection/testing/syntheticPdf.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.pdfSelection.testing.syntheticPdf"
language: "TypeScript"
area: "TypeScript/components/pdfSelection/testing"
source_path: "apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticPdf.ts"
source_paths:
  - "apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticPdf.ts"
activation_kind: "vitest-support"
activation_evidence: "Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/components/pdfSelection/testing/syntheticPdf.ts`

Area: [[Reference/Desktop/TypeScript/components/pdfSelection/testing/_area|TypeScript/components/pdfSelection/testing]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides shared `syntheticPdf` state or utility behavior for desktop components.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticPdf.ts](../../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticPdf.ts) |
| Source lines | 183 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/pdfSelection/testing/_area|TypeScript/components/pdfSelection/testing]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/components/pdfSelection/testing/syntheticPdf|src/components/pdfSelection/testing/syntheticPdf.ts]]

## Public API

- `export type PdfFont = "Helvetica" | "Courier" | "Times-Roman" | "Type3"` — type, line 11
- `export interface PdfText` — interface, line 15
- `export interface PdfPageSpec` — interface, line 24
- `export function fontKey(font: PdfFont): string` — function, line 40
- `export function buildPdf(pages: readonly PdfPageSpec[]): Uint8Array` — function, line 49
- `export interface ParsedPage` — interface, line 110
- `export interface PaintedPage` — interface, line 123
- `export async function readPdf(bytes: Uint8Array): Promise<ParsedPage[]>` — function, line 131
- `export async function paintPdf(bytes: Uint8Array): Promise<` — function, line 159

## Internal implementation anchors

- `const FONT_KEYS: Record<PdfFont, string> =` — const, line 13
- `function escapePdf(text: string): string` — function, line 44
- `const objects: string[] = []` — const, line 50
- `const add = (body: string)` — const, line 51
- `const font = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")` — const, line 55
- `const image = add( "<< /Type /XObject /Subtype /Image /Width 2 /Height 2 /ColorSpace /DeviceGray /BitsPerComponent 8 /Length 4 >>\nstream\n °° \nendstream", )` — const, line 56
- `const courier = add("<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>")` — const, line 59
- `const times = add("<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman /Encoding /WinAnsiEncoding >>")` — const, line 60
- `const blank = "0 0 0 0 0 0 d1"` — const, line 61
- `const glyph = add(`<< /Length $` — const, line 62
- `const type3 = add( `<< /Type /Font /Subtype /Type3 /FontBBox [0 0 1000 1000] /FontMatrix [0.001 0 0 0.001 0 0] ` + `/CharProcs << /space $` — const, line 63
- `const formStream = "BT /F2 10 Tf 0 0 Td (Form) Tj ET"` — const, line 69
- `const form = add( `<< /Type /XObject /Subtype /Form /BBox [0 0 200 50] /Matrix [1 0 0 1 300 100] ` + `/Resources << /Font << /F2 $` — const, line 70
- `const contents = pages.map((page)` — const, line 74
- `const height = page.height ?? 792` — const, line 75
- `const width = page.width ?? 612` — const, line 76
- `const ops = page.scanned ? [`q $` — const, line 77
- `const stream = ops.join("\n")` — const, line 83
- `const pagesId = objects.length + pages.length + 1` — const, line 86
- `const kids = pages.map((page, index)` — const, line 87
- `const pagesObject = add(`<< /Type /Pages /Kids [$` — const, line 94
- `const catalog = add(`<< /Type /Catalog /Pages $` — const, line 96
- `let out = "%PDF-1.4\n"` — let, line 97
- `const offsets: number[] = []` — const, line 98
- `const xref = out.length` — const, line 103
- `const pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs")` — const, line 132
- `const task = pdfjs.getDocument(` — const, line 133
- `const doc = await task.promise` — const, line 134
- `const out: ParsedPage[] = []` — const, line 135
- `const page = await doc.getPage(number)` — const, line 137
- `const viewport = page.getViewport(` — const, line 138
- `const content = await page.getTextContent()` — const, line 139
- `const pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs")` — const, line 160
- `const task = pdfjs.getDocument(` — const, line 161
- `const doc = await task.promise` — const, line 162
- `const pages: PaintedPage[] = []` — const, line 163
- `const page = await doc.getPage(number)` — const, line 165
- `const opList = await page.getOperatorList(` — const, line 166
- `const fonts: PaintedPage["fonts"] = new Map()` — const, line 167
- `const name = String((opList.argsArray[index] as unknown[])[0])` — const, line 170
- `const font = page.commonObjs.get(name) as` — const, line 171

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/pdfSelection/testing/syntheticBook|src/components/pdfSelection/testing/syntheticBook.ts]] — import-or-re-export: `PdfPageSpec`, `PdfText`; references `PdfPageSpec`, `PdfText`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `pdfjs-dist/legacy/build/pdf.mjs`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/pdfSelection/perf.test.ts](../../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/perf.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/pdfSelection/model.test.ts](../../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/pdfSelection/fonts.test.ts](../../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/fonts.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/pdfSelection/arxiv.test.ts](../../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/arxiv.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/PdfReaderPane.selection.test.tsx](../../../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.selection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticPdf.ts](../../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticPdf.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
