---
title: "Desktop module · src/components/pdfSelection/testing/syntheticBook.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.pdfSelection.testing.syntheticBook"
language: "TypeScript"
area: "TypeScript/components/pdfSelection/testing"
source_path: "apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts"
source_paths:
  - "apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts"
source_commit: "b1087be0a01909d5363e9c41f140e27673801640"
source_commit_timestamp: "2026-10-15T14:19:42-04:00"
source_worktree_state: "clean"
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

# `src/components/pdfSelection/testing/syntheticBook.ts`

Area: [[Reference/Desktop/TypeScript/components/pdfSelection/testing/_area|TypeScript/components/pdfSelection/testing]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides shared `syntheticBook` state or utility behavior for desktop components.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts](../../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts) |
| Source lines | 187 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/pdfSelection/testing/_area|TypeScript/components/pdfSelection/testing]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |
| Worktree state | `clean` |
| Source commit | `b1087be0a01909d5363e9c41f140e27673801640` |
| Commit timestamp | `2026-10-15T14:19:42-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/components/pdfSelection/testing/syntheticBook|src/components/pdfSelection/testing/syntheticBook.ts]]

## Public API

- `export const SYNTHETIC_PAGES: PdfPageSpec[] = [` — const, line 161
- `export const SYNTHETIC_BLOCKS: ReaderPdfBlockDto[] = (()` — const, line 169
- `export function linePoint(spanId: string, line: number, fraction: number):` — function, line 177

## Internal implementation anchors

- `interface Para` — interface, line 14
- `function paraTexts(para: Para): PdfText[]` — function, line 29
- `function paraBox(para: Para): number[]` — function, line 36
- `const lineCount = para.cells ? Math.max(...para.cells.map((cell)` — const, line 37
- `const lastBaseline = para.y + (lineCount - 1) * para.leading` — const, line 38
- `const PAGE0: Para[] = [` — const, line 42
- `const PAGE1: Para[] = [` — const, line 79
- `const PAGE2_BLOCKS: ReaderPdfBlockDto[] = [` — const, line 133
- `function blocksOf(page: number, paras: Para[]): ReaderPdfBlockDto[]` — function, line 148
- `const page0 = blocksOf(0, PAGE0)` — const, line 170
- `const order = ["h0", "s1", "s2", "s3", "s4"]` — const, line 171
- `const all: Array<[number, Para]> = [...PAGE0.map((p)` — const, line 178
- `const found = all.find(([, para])` — const, line 179
- `const baseline = para.y + line * para.leading` — const, line 182
- `const text = para.lines[line] ?? ""` — const, line 183
- `const width = text.length * para.size * 0.5` — const, line 185

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

No live desktop source file directly imports this module. Do not infer dormancy: it can still be an implicit entry, worker, ambient declaration, fixture, or runtime-dispatched surface.

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderPdfBlockDto`
- [[Reference/Desktop/TypeScript/components/pdfSelection/testing/syntheticPdf|src/components/pdfSelection/testing/syntheticPdf.ts]] — import-or-re-export; imports `PdfPageSpec`, `PdfText`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/pdfSelection/model.test.ts](../../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/pdfSelection/arxiv.test.ts](../../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/arxiv.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/PdfReaderPane.selection.test.tsx](../../../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.selection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts](../../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
