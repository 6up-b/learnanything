---
title: "Desktop module · src/screens/desks/menu/model.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.menu.model"
language: "TypeScript"
area: "TypeScript/screens/desks/menu"
source_path: "apps/learnloop-tauri/src/screens/desks/menu/model.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/menu/model.ts"
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

# `src/screens/desks/menu/model.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/menu/_area|TypeScript/screens/desks/menu]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `MenuObjectKind`, `MenuObject`, `captureNodes`, `passageIds` and related exports within the desktop's TypeScript/screens/desks/menu ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/menu/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/model.ts) |
| Source lines | 294 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/menu/_area|TypeScript/screens/desks/menu]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/menu/model|src/screens/desks/menu/model.ts]]

## Public API

- `export type MenuObjectKind = MenuObjectInput["objectKind"]` — type, line 8
- `export interface MenuObject` — interface, line 11
- `export function captureNodes(object: MenuObject): Array<` — function, line 36
- `export function passageIds(object: MenuObject): string[]` — function, line 43
- `export function objectInput(object: MenuObject, deskId: string | null): MenuObjectInput` — function, line 49
- `export interface MenuVerdict` — interface, line 78
- `export function verdictFor(verdict: MenuVerdict, verb?: VerbId): boolean` — function, line 84
- `export function headerLine(object: MenuObject, withheld: boolean | null = null): string` — function, line 88
- `export type VerbId = | "ask" | "note" | "append" | "carry" | "open_beside" | "find" | "compare" | "show_me" | "make_practice" | "teach_me" | "submit" | "new_desk" | "gather" | "share_slot" | "own_slot" | "knows"` — type, line 98
- `export interface VerbSpec` — interface, line 102
- `export const VERBS: VerbSpec[] = [` — const, line 110
- `export function needsClearance(id: VerbId): boolean` — function, line 135
- `export function verbsFor(kind: MenuObjectKind): VerbSpec[]` — function, line 140
- `export function hasPassage(object: MenuObject): boolean` — function, line 145
- `export interface MenuRow` — interface, line 150
- `export function shownPromoted(rows: PromotedRowDto[], dismissed: ReadonlySet<string>, cap = 4): PromotedRowDto[]` — function, line 172
- `export function promotedReason(row: PromotedRowDto): string` — function, line 177
- `export const MENU_SIZES =` — const, line 184
- `export function placeMenu(at:` — function, line 187
- `export function placeSubmenu(row:` — function, line 194
- `export function objectAt(target: Element, kindOf: (windowId: string)` — function, line 202

## Internal implementation anchors

- `const ids = object.spanIds?.length ? object.spanIds : object.spanId ? [object.spanId] : []` — const, line 38
- `const ids = passageIds(object)` — const, line 50
- `const KIND_LABEL: Record<MenuObjectKind, string> =` — const, line 65
- `const words = (object.selection || object.text).replace(/\s+/g, " ").trim()` — const, line 91
- `const clipped = words.length > 46 ? `$` — const, line 92
- `const NAVIGATION_VERBS: readonly VerbId[] = ["open_beside", "knows", "new_desk", "gather", "share_slot", "own_slot"]` — const, line 130
- `const LOCAL_VERBS: readonly VerbId[] = ["note"]` — const, line 134
- `const left = Math.max(MENU_SIZES.edge, Math.min(at.x + 2, viewport.w - size.w - MENU_SIZES.edge))` — const, line 188
- `const top = Math.max(MENU_SIZES.top, Math.min(at.y + 2, viewport.h - size.h - MENU_SIZES.edge))` — const, line 189
- `const host = target.closest(`[$` — const, line 203
- `const windowId = host?.getAttribute(WINDOW_ATTRIBUTE) ?? null` — const, line 204
- `const head = target.closest(".desk-pane-head")` — const, line 206
- `const source = sourceOf(windowId)` — const, line 209
- `const spanId = source ? inView(windowId) : null` — const, line 210
- `const pad = target.closest("[data-pad]")` — const, line 215
- `const line = target.closest("[data-block]")` — const, line 217
- `const selected = selectionWithin(pad, doc, "[data-block]", (element)` — const, line 218
- `const blockIds = [...new Set([line?.getAttribute("data-block"), ...(selected?.ids ?? [])].filter((id): id is string` — const, line 219
- `const selection = selected?.text` — const, line 220
- `const source = sourceOf(windowId)` — const, line 227
- `const annotation = target.closest("[data-annotation-id]")` — const, line 229
- `const passage = target.closest("[data-span-id], [data-transcript-span]")` — const, line 230
- `const annotationSpan = annotation ? (passage ? spanOf(passage) : annotation.getAttribute("data-annotation-span") || undefined) : undefined` — const, line 232
- `const selected = selectionWithin(host, doc, "[data-span-id], [data-transcript-span], [data-annotation-span]", spanOf)` — const, line 234
- `const selection = selected &&` — const, line 235
- `const isNote = annotation.getAttribute("data-annotation-kind") === "note"` — const, line 238
- `const spanId = spanOf(passage)` — const, line 249
- `const cue = passage.hasAttribute("data-transcript-span") || kindOf(windowId) === "video"` — const, line 250
- `const tAttr = passage.getAttribute("data-t") ?? passage.closest("[data-t]")?.getAttribute("data-t")` — const, line 251
- `function spanOf(element: Element): string | undefined` — function, line 262
- `function annotationSpans(element: Element): string[]` — function, line 266
- `const spans = element.getAttribute("data-annotation-spans")` — const, line 267
- `function selectionWithin(host: Element | null, doc: Document, selector: string, idOf: (element: Element)` — function, line 271
- `const selection = doc.getSelection?.()` — const, line 272
- `const range = selection.getRangeAt(0)` — const, line 274
- `const text = range.toString().replace(/\s+/g, " ").trim()` — const, line 276
- `const ids: string[] = []` — const, line 278
- `const slices: Array<` — const, line 279
- `const id = idOf(element)` — const, line 281
- `const part = doc.createRange()` — const, line 284
- `const quote = part.toString().replace(/\s+/g, " ").trim()` — const, line 288

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `MenuObject`, `MenuVerdict`, `captureNodes`, `hasPassage`, `headerLine`, `objectAt`, `objectInput`, `passageIds`, `verdictFor`; references `MenuObject`, `MenuVerdict`, `captureNodes`, `hasPassage`, `headerLine`, `objectAt`, `objectInput`, `passageIds`, `verdictFor`
- [[Reference/Desktop/TypeScript/screens/desks/menu/ContextMenu|src/screens/desks/menu/ContextMenu.tsx]] — import-or-re-export: `MENU_SIZES`, `MenuRow`, `placeMenu`, `placeSubmenu`, `promotedReason`, `shownPromoted`; references `MENU_SIZES`, `MenuRow`, `placeMenu`, `placeSubmenu`, `promotedReason`, `shownPromoted`
- [[Reference/Desktop/TypeScript/screens/desks/menu/verbs|src/screens/desks/menu/verbs.ts]] — import-or-re-export: `MenuObject`, `MenuRow`, `VerbId`, `captureNodes`, `hasPassage`, `needsClearance`, `objectInput`, `passageIds`, `verbsFor`; references `MenuObject`, `MenuRow`, `VerbId`, `captureNodes`, `hasPassage`, `needsClearance`, `objectInput`, `passageIds`, `verbsFor`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadOverlays|src/screens/desks/pads/PadOverlays.tsx]] — import-or-re-export: `MenuRow`; references `MenuRow`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `MenuObjectInput`, `PromotedRowDto`
- [[Reference/Desktop/TypeScript/screens/desks/keys/listeners|src/screens/desks/keys/listeners.ts]] — import-or-re-export; imports `WINDOW_ATTRIBUTE`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/menu/verbs.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/verbs.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/menu/model.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/menu/ContextMenu.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/ContextMenu.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/checks/gates.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/gates.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/menu/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/model.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
