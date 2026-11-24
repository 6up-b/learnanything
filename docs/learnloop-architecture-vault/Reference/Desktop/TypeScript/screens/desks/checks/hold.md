---
title: "Desktop module · src/screens/desks/checks/hold.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.checks.hold"
language: "TypeScript"
area: "TypeScript/screens/desks/checks"
source_path: "apps/learnloop-tauri/src/screens/desks/checks/hold.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/checks/hold.ts"
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

# `src/screens/desks/checks/hold.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SAFE_ATTR`, `PASSAGE_TEXT_ATTR`, `REGION_ATTR`, `QUIET_ATTR` and related exports within the desktop's TypeScript/screens/desks/checks ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/checks/hold.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/hold.ts) |
| Source lines | 349 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/checks/hold|src/screens/desks/checks/hold.ts]]

## Public API

- `export const SAFE_ATTR = "data-check-safe"` — const, line 23
- `export const PASSAGE_TEXT_ATTR = "data-passage-text"` — const, line 24
- `export const REGION_ATTR = "data-check-region"` — const, line 26
- `export const QUIET_ATTR = "data-check-region-quiet"` — const, line 28
- `export const CONTENT_ATTR = "data-check-content"` — const, line 30
- `export const DESK_REGION = "the desk"` — const, line 41
- `export interface HoldWindow` — interface, line 43
- `export interface HoldInput` — interface, line 48
- `export interface HeldNamed` — interface, line 60
- `export interface HeldRegion` — interface, line 66
- `export interface HoldResult` — interface, line 76
- `export function printOf(element: Element): string` — function, line 93
- `export class Holder` — class, line 121

## Internal implementation anchors

- `const LABELS = ["title", "aria-label", "aria-description", "aria-roledescription", "aria-valuetext", "placeholder", "alt"] as const` — const, line 33
- `const HELD = "ck-held"` — const, line 35
- `const NAMED = "ck-veiled"` — const, line 36
- `const NAMED_LOOK = "veiled"` — const, line 37
- `const UNVEIL_MS = 700` — const, line 38
- `interface Stash` — interface, line 85
- `const parts: string[] = []` — const, line 94
- `const own = element.getAttribute(CONTENT_ATTR)` — const, line 95
- `function regionHere(element: Element, outer: string): string` — function, line 103
- `const named = element.getAttribute(REGION_ATTR)` — const, line 104
- `const windowId = element.getAttribute("data-desk-window")` — const, line 106
- `function attr(value: string): string` — function, line 112
- `function passageOf(element: Element): Element | null` — function, line 116
- `const namedOf = new Map<Element, CheckVeilRefDto>()` — const, line 126
- `const selector = veilSelector(ref)` — const, line 128
- `const changed: string[] = []` — const, line 132
- `const printed: HoldResult["printed"] = []` — const, line 133
- `const allowed = new Set<Element>()` — const, line 136
- `const selector = veilSelector(ref)` — const, line 140
- `const elements = [...root.querySelectorAll(selector)]` — const, line 142
- `const now = elements.map(printOf).join("#")` — const, line 143
- `const key = refKey(ref)` — const, line 144
- `const openRegions = new Map<string, Element>()` — const, line 154
- `const host = region.startsWith("window:") ? root.querySelector(`[data-desk-window="$` — const, line 156
- `const now = host ? printOf(host) : ""` — const, line 158
- `const containers = new Set<Element>()` — const, line 163
- `const markUp = (from: Element, into: Set<Element>)` — const, line 164
- `const namedAbove = new Set<Element>()` — const, line 171
- `const holdNow = new Map<Element,` — const, line 174
- `const containerNow = new Set<Element>()` — const, line 175
- `const walk = (element: Element, named: CheckVeilRefDto | null, outer: string)` — const, line 176
- `const region = regionHere(element, outer)` — const, line 178
- `const own = namedOf.get(element) ?? named` — const, line 179
- `const next = holdNow.get(element)` — const, line 204
- `const labels = this.containers.get(element) ?? new Map<string, string | null>()` — const, line 216
- `const named: HeldNamed[] = []` — const, line 223
- `const regions = new Map<string, HeldRegion>()` — const, line 224
- `const entry = regions.get(at.region) ??` — const, line 230
- `const host = entry.windowId ? root.querySelector(`[data-desk-window="$` — const, line 239
- `const passage = passageOf(text)` — const, line 258
- `const host = text.closest("[data-desk-window]")` — const, line 259
- `const windowId = host.getAttribute("data-desk-window") ?? ""` — const, line 261
- `const window = input.windows.get(windowId)` — const, line 262
- `const spanId = passage.getAttribute("data-span-id") ?? passage.getAttribute("data-transcript-span") ?? ""` — const, line 264
- `const passage = element.matches("[data-span-id], [data-transcript-span]") ? element : null` — const, line 271
- `const host = passage.closest("[data-desk-window]")` — const, line 273
- `const windowId = host?.getAttribute("data-desk-window") ?? ""` — const, line 274
- `const window = input.windows.get(windowId)` — const, line 275
- `const spanId = passage.getAttribute("data-span-id") ?? passage.getAttribute("data-transcript-span") ?? ""` — const, line 276
- `let stash = this.held.get(element)` — let, line 281
- `const look = named ? [NAMED, NAMED_LOOK] : [HELD]` — const, line 291
- `const wasNamed = element.classList.contains(NAMED)` — const, line 302
- `const active = root.ownerDocument.activeElement` — const, line 320
- `const answer = root.querySelector<HTMLElement>("[data-check-card] textarea")` — const, line 324
- `function stripLabels(element: Element, stash: Map<string, string | null>): void` — function, line 332
- `const value = element.getAttribute(name)` — const, line 334
- `function restoreLabels(element: Element, stash: Map<string, string | null>): void` — function, line 344

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `SAFE_ATTR`; references `SAFE_ATTR`
- [[Reference/Desktop/TypeScript/screens/desks/checks/CheckCard|src/screens/desks/checks/CheckCard.tsx]] — import-or-re-export: `SAFE_ATTR`; references `SAFE_ATTR`
- [[Reference/Desktop/TypeScript/screens/desks/checks/VeilLayer|src/screens/desks/checks/VeilLayer.tsx]] — import-or-re-export: `HeldRegion`, `HoldResult`, `HoldWindow`, `Holder`, `SAFE_ATTR`, `printOf`; references `HeldRegion`, `HoldResult`, `HoldWindow`, `Holder`, `SAFE_ATTR`, `printOf`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CheckVeilRefDto`
- [[Reference/Desktop/TypeScript/screens/desks/checks/model|src/screens/desks/checks/model.ts]] — import-or-re-export; imports `VEIL_LABEL`, `passagesCanShow`, `refKey`, `veilSelector`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/checks/checks.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/checks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/checks/hold.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/hold.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
