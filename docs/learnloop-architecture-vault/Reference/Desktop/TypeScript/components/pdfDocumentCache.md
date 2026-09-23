---
title: "Desktop module · src/components/pdfDocumentCache.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.pdfDocumentCache"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/pdfDocumentCache.ts"
source_paths:
  - "apps/learnloop-tauri/src/components/pdfDocumentCache.ts"
source_commit: "33c7456b0f78caa01172f6170de7727f002513c3"
source_commit_timestamp: "2026-09-23T12:06:06-04:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "A static TypeScript import path reaches this file from the Vite entry src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/components/pdfDocumentCache.ts`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides shared `pdfDocumentCache` state or utility behavior for desktop components.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/pdfDocumentCache.ts](../../../../../../apps/learnloop-tauri/src/components/pdfDocumentCache.ts) |
| Source lines | 124 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `33c7456b0f78caa01172f6170de7727f002513c3` |
| Commit timestamp | `2026-09-23T12:06:06-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/pdfDocumentCache|src/components/pdfDocumentCache.ts]]

## Public API

- `export interface CachedPdfDocument` — interface, line 18
- `export function acquirePdfDocument(fileUrl: string): Promise<CachedPdfDocument>` — function, line 99
- `export function clearPdfDocuments(): void` — function, line 115

## Internal implementation anchors

- `const MAX_DOCS = 3` — const, line 16
- `interface Entry extends CachedPdfDocument` — interface, line 24
- `const documents = new Map<string, Entry>()` — const, line 30
- `const loading = new Map<string, Promise<CachedPdfDocument>>()` — const, line 31
- `const pendingFetches = new Set<AbortController>()` — const, line 32
- `const pendingTasks = new Set<PDFDocumentLoadingTask>()` — const, line 33
- `const destruction = new WeakMap<PDFDocumentLoadingTask, Promise<void>>()` — const, line 34
- `function destroyTask(task: PDFDocumentLoadingTask): Promise<void>` — function, line 36
- `const existing = destruction.get(task)` — const, line 37
- `const promise = Promise.resolve().then(()` — const, line 40
- `let generation = 0` — let, line 46
- `function evictBeyondLimit(): void` — function, line 48
- `const stale = [...documents.entries()].sort((a, b)` — const, line 50
- `async function load(fileUrl: string): Promise<CachedPdfDocument>` — function, line 58
- `const startedIn = generation` — const, line 59
- `const controller = new AbortController()` — const, line 60
- `let data: Uint8Array` — let, line 62
- `let pdfjs: typeof import("pdfjs-dist")` — let, line 63
- `const task = pdfjs.getDocument(` — const, line 73
- `let doc: PDFDocumentProxy` — let, line 75
- `const entry: Entry =` — const, line 84
- `const existing = documents.get(fileUrl)` — const, line 85
- `const cached = documents.get(fileUrl)` — const, line 100
- `const inFlight = loading.get(fileUrl)` — const, line 105
- `const promise = load(fileUrl).finally(()` — const, line 107

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `clearPdfDocuments`; references `clearPdfDocuments`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `acquirePdfDocument`; references `acquirePdfDocument`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `pdfjs-dist`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/pdfDocumentCache.test.ts](../../../../../../apps/learnloop-tauri/src/components/pdfDocumentCache.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/pdfDocumentCache.ts](../../../../../../apps/learnloop-tauri/src/components/pdfDocumentCache.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
