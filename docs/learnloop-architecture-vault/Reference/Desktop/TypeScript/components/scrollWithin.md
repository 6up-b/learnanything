---
title: "Desktop module · src/components/scrollWithin.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.scrollWithin"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/scrollWithin.ts"
source_paths:
  - "apps/learnloop-tauri/src/components/scrollWithin.ts"
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

# `src/components/scrollWithin.ts`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides shared `scrollWithin` state or utility behavior for desktop components.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/scrollWithin.ts](../../../../../../apps/learnloop-tauri/src/components/scrollWithin.ts) |
| Source lines | 108 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/components/scrollWithin|src/components/scrollWithin.ts]]

## Public API

- `export type ScrollBlock = "start" | "center" | "end" | "nearest"` — type, line 13
- `export interface ScrollWithinOptions` — interface, line 15
- `export function scrollIntoViewWithin(target: Element | null | undefined, options: ScrollWithinOptions =` — function, line 88

## Internal implementation anchors

- `const USER_SCROLLABLE = /^(auto|scroll|overlay)$/` — const, line 20
- `function isUserScrollable(element: Element): boolean` — function, line 22
- `const view = element.ownerDocument.defaultView` — const, line 23
- `function pixels(value: string | null | undefined): number` — function, line 28
- `const parsed = Number.parseFloat(value ?? "")` — const, line 29
- `function stickyCover(container: HTMLElement, target: Element):` — function, line 37
- `const view = container.ownerDocument.defaultView` — const, line 38
- `const own = view.getComputedStyle(container)` — const, line 40
- `let top = 0` — let, line 41
- `let bottom = 0` — let, line 42
- `const style = view.getComputedStyle(child)` — const, line 45
- `const height = child.getBoundingClientRect().height` — const, line 47
- `function targetScrollTop(container: HTMLElement, top: number, height: number, block: ScrollBlock, marginTop: number, cover:` — function, line 58
- `const box = container.getBoundingClientRect()` — const, line 60
- `const view = container.clientHeight` — const, line 61
- `const clear = Math.max(0, view - cover.top - cover.bottom)` — const, line 62
- `const offset = container.scrollTop + (top - box.top - container.clientTop)` — const, line 63
- `const visibleTop = container.scrollTop + cover.top` — const, line 72
- `const visibleBottom = container.scrollTop + view - cover.bottom` — const, line 73
- `function clampScrollTop(container: HTMLElement, value: number): number` — function, line 81
- `const max = container.scrollHeight - container.clientHeight` — const, line 82
- `const block = options.block ?? "start"` — const, line 90
- `const behavior = options.behavior ?? "auto"` — const, line 91
- `const doc = target.ownerDocument` — const, line 92
- `const view = doc.defaultView` — const, line 93
- `const marginTop = view ? pixels(view.getComputedStyle(target).scrollMarginTop) : 0` — const, line 94
- `const rect = target.getBoundingClientRect()` — const, line 95
- `let shift = 0` — let, line 98
- `const current = node.scrollTop` — const, line 101
- `const next = clampScrollTop(node, targetScrollTop(node, rect.top - shift, rect.height, block, marginTop, stickyCover(node, target)))` — const, line 102

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `scrollIntoViewWithin`; references `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `scrollIntoViewWithin`; references `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] — import-or-re-export: `scrollIntoViewWithin`; references `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export: `scrollIntoViewWithin`; references `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/screens/reader/ReadingPathCard|src/screens/reader/ReadingPathCard.tsx]] — import-or-re-export: `scrollIntoViewWithin`; references `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `scrollIntoViewWithin`; references `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export: `scrollIntoViewWithin`; references `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/screens/reader/useSidePane|src/screens/reader/useSidePane.ts]] — import-or-re-export: `scrollIntoViewWithin`; references `scrollIntoViewWithin`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/readingPathsReader.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/readingPathsReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/figureProvenanceReader.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureProvenanceReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/ReaderScreen.recapReview.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.recapReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/ReaderScreen.followsLearner.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.followsLearner.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/scrollWithin.test.ts](../../../../../../apps/learnloop-tauri/src/components/scrollWithin.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/PdfReaderPane.scroll.test.tsx](../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.scroll.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/PdfReaderPane.marks.test.tsx](../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.marks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/scrollWithin.ts](../../../../../../apps/learnloop-tauri/src/components/scrollWithin.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
