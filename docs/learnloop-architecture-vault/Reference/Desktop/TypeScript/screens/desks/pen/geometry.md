---
title: "Desktop module · src/screens/desks/pen/geometry.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pen.geometry"
language: "TypeScript"
area: "TypeScript/screens/desks/pen"
source_path: "apps/learnloop-tauri/src/screens/desks/pen/geometry.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pen/geometry.ts"
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

# `src/screens/desks/pen/geometry.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `PASSAGE`, `LocalRect`, `caretAt`, `passages` and related exports within the desktop's TypeScript/screens/desks/pen ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pen/geometry.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/geometry.ts) |
| Source lines | 228 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pen/InkLine|src/screens/desks/pen/InkLine.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pen/geometry|src/screens/desks/pen/geometry.ts]]

## Public API

- `export const PASSAGE = "[data-span-id]"` — const, line 7
- `export interface LocalRect` — interface, line 9
- `export function caretAt(host: HTMLElement, x: number, y: number, doc: Document = host.ownerDocument): Range | null` — function, line 22
- `export function passages(host: HTMLElement): HTMLElement[]` — function, line 45
- `export function pageOf(host: HTMLElement): RecognizerPage` — function, line 49
- `export function rangeBetween(host: HTMLElement, a: Point, b: Point): Range | null` — function, line 63
- `export function rangeOfQuote(host: HTMLElement, spanId: string, quote: string): Range | null` — function, line 96
- `export function inPolygon(x: number, y: number, polygon: readonly Point[]): boolean` — function, line 124
- `export function wordsInLoop(host: HTMLElement, loop: readonly Point[]): Range | null` — function, line 135
- `export function passagesSpanned(host: HTMLElement, box: Box): HTMLElement[]` — function, line 164
- `export function passageBeside(host: HTMLElement, box: Box): HTMLElement | null` — function, line 172
- `export function toLocal(host: HTMLElement, x: number, y: number): Point` — function, line 194
- `export function toClient(host: HTMLElement, x: number, y: number): Point` — function, line 199
- `export function localRects(host: HTMLElement, rects: Iterable<DOMRect>): LocalRect[]` — function, line 204
- `export function distanceToPolyline(p: Point, line: readonly Point[]): number` — function, line 215

## Internal implementation anchors

- `type CaretDoc = Document &` — type, line 16
- `const caretDoc = doc as CaretDoc` — const, line 23
- `let range: Range | null = null` — let, line 24
- `const position = caretDoc.caretPositionFromPoint(x, y)` — const, line 28
- `const passage = (range.startContainer instanceof Element ? range.startContainer : range.startContainer.parentElement)?.closest(PASSAGE)` — const, line 35
- `function caretLine(range: Range): LineBox | null` — function, line 39
- `const rect = range.getClientRects?.()[0] ?? range.getBoundingClientRect?.()` — const, line 40
- `const column = passages(host).map((element)` — const, line 52
- `const range = caretAt(host, x, y)` — const, line 56
- `const start = caretAt(host, a.x, a.y)` — const, line 64
- `const end = caretAt(host, b.x, b.y)` — const, line 65
- `const range = host.ownerDocument.createRange()` — const, line 67
- `const isWord = (ch: string | undefined)` — const, line 77
- `const text = range.startContainer.textContent ?? ""` — const, line 79
- `let at = range.startOffset` — let, line 80
- `const text = range.endContainer.textContent ?? ""` — const, line 85
- `let at = range.endOffset` — let, line 86
- `const element = passages(host).find((each)` — const, line 97
- `const wanted = quote.replace(/\s+/g, " ").trim()` — const, line 98
- `const doc = host.ownerDocument` — const, line 100
- `const walker = doc.createTreeWalker(element, NodeFilter.SHOW_TEXT)` — const, line 101
- `let folded = ""` — let, line 103
- `const from: Array<` — const, line 104
- `const text = node.data` — const, line 106
- `const space = /\s/.test(text[i])` — const, line 108
- `const at = folded.indexOf(wanted)` — const, line 114
- `const first = from[at]` — const, line 116
- `const last = from[at + wanted.length - 1]` — const, line 117
- `const range = doc.createRange()` — const, line 118
- `let inside = false` — let, line 125
- `const a = polygon[i]` — const, line 127
- `const b = polygon[j]` — const, line 128
- `let first: [Node, number] | null = null` — let, line 136
- `let last: [Node, number] | null = null` — let, line 137
- `const doc = host.ownerDocument` — const, line 138
- `const walker = doc.createTreeWalker(passage, NodeFilter.SHOW_TEXT)` — const, line 140
- `const text = (node as Text).data` — const, line 142
- `const at = match.index ?? 0` — const, line 144
- `const word = doc.createRange()` — const, line 145
- `const rect = word.getBoundingClientRect()` — const, line 148
- `const range = doc.createRange()` — const, line 157
- `const rect = element.getBoundingClientRect()` — const, line 166
- `const all = passages(host).filter((element)` — const, line 173
- `const overlapping = all.find((element)` — const, line 174
- `const rect = element.getBoundingClientRect()` — const, line 175
- `const middle = (box.y0 + box.y1) / 2` — const, line 179
- `let best: HTMLElement | null = null` — let, line 180
- `let distance = Infinity` — let, line 181
- `const rect = element.getBoundingClientRect()` — const, line 183
- `const d = middle < rect.top ? rect.top - middle : middle > rect.bottom ? middle - rect.bottom : 0` — const, line 184
- `const rect = host.getBoundingClientRect()` — const, line 195
- `const rect = host.getBoundingClientRect()` — const, line 200
- `const out: LocalRect[] = []` — const, line 205
- `const at = toLocal(host, rect.left, rect.top)` — const, line 208
- `let best = Infinity` — let, line 217
- `const a = line[i - 1]` — const, line 219
- `const b = line[i]` — const, line 220
- `const dx = b.x - a.x` — const, line 221
- `const dy = b.y - a.y` — const, line 222
- `const length = dx * dx + dy * dy` — const, line 223
- `const t = length ? Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / length)) : 0` — const, line 224

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/pen/InkLine|src/screens/desks/pen/InkLine.tsx]] — import-or-re-export: `distanceToPolyline`; references `distanceToPolyline`
- [[Reference/Desktop/TypeScript/screens/desks/pen/PenLayer|src/screens/desks/pen/PenLayer.tsx]] — import-or-re-export: `LocalRect`, `distanceToPolyline`, `localRects`, `pageOf`, `passageBeside`, `passages`, `passagesSpanned`, `rangeBetween`, `rangeOfQuote`, `toClient`, `toLocal`, `wordsInLoop`; references `LocalRect`, `distanceToPolyline`, `localRects`, `pageOf`, `passageBeside`, `passages`, `passagesSpanned`, `rangeBetween`, `rangeOfQuote`, `toClient`, `toLocal`, `wordsInLoop`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/desks/pen/recognizer|src/screens/desks/pen/recognizer.ts]] — import-or-re-export; imports `Box`, `LineBox`, `Point`, `RECOGNIZER`, `RecognizerPage`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pen/geometry.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/geometry.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
