---
title: "Desktop module · src/screens/desks/checks/VeilLayer.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.checks.VeilLayer"
language: "TypeScript"
area: "TypeScript/screens/desks/checks"
source_path: "apps/learnloop-tauri/src/screens/desks/checks/VeilLayer.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/checks/VeilLayer.tsx"
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

# `src/screens/desks/checks/VeilLayer.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `VeilLayer` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/checks/VeilLayer.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/VeilLayer.tsx) |
| Source lines | 248 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/checks/VeilLayer|src/screens/desks/checks/VeilLayer.tsx]]

## Public API

- `export function dialogPlace(at:` — function, line 91
- `export type HoldWindows = ReadonlyMap<string, HoldWindow>` — type, line 115
- `export function VeilLayer(` — function, line 119

## Internal implementation anchors

- `interface Pill` — interface, line 16
- `const OCCLUDERS = "[data-companion-dock], [data-check-card='overlay'], [data-desk-search], .goalband"` — const, line 26
- `function shownBox(element: Element): DOMRect | null` — function, line 29
- `const box = element.getBoundingClientRect()` — const, line 30
- `const frames = [element.parentElement?.closest("[data-desk-pane-body]"), element.closest("[data-desk-window]")] .filter((each): each is Element` — const, line 32
- `const left = Math.max(box.left, ...frames.map((f)` — const, line 35
- `const right = Math.min(box.right, ...frames.map((f)` — const, line 36
- `const top = Math.max(box.top, ...frames.map((f)` — const, line 37
- `const bottom = Math.min(box.bottom, ...frames.map((f)` — const, line 38
- `function placeOf(element: Element, root: ParentNode):` — function, line 45
- `const shown = shownBox(element)` — const, line 46
- `const at =` — const, line 48
- `const r = cover.getBoundingClientRect()` — const, line 51
- `function pillsOf(result: HoldResult, root: ParentNode, laidOut: boolean, judging: boolean): Pill[]` — function, line 57
- `const pills: Pill[] = []` — const, line 58
- `const at = laidOut ? placeOf(element, root) :` — const, line 61
- `let best:` — let, line 68
- `const shown = shownBox(element)` — const, line 74
- `const at = placeOf(element, root)` — const, line 76
- `const EDGE = 8` — const, line 86
- `const PILL_GAP = 18` — const, line 87
- `const half = size.width / 2` — const, line 93
- `const left = Math.min(Math.max(at.left, EDGE + half), Math.max(EDGE + half, viewport.width - EDGE - half))` — const, line 94
- `const below = at.top + PILL_GAP` — const, line 95
- `const above = at.top - PILL_GAP - size.height` — const, line 96
- `const top = below + size.height <= viewport.height - EDGE ? below : above >= EDGE ? above : Math.max(EDGE, viewport.height - EDGE - size.height)` — const, line 97
- `function samePills(a: readonly Pill[], b: readonly Pill[]): boolean` — function, line 103
- `function printsOf(root: Element | null, ref: CheckVeilRefDto): string` — function, line 109
- `const selector = veilSelector(ref)` — const, line 110
- `const holding = desk.holding()` — const, line 121
- `const version = desk.getVersion()` — const, line 122
- `const askRef = useRef<HTMLDivElement | null>(null)` — const, line 125
- `const dialog = askRef.current` — const, line 128
- `const place = ()` — const, line 130
- `const box = dialog.getBoundingClientRect()` — const, line 131
- `const at = dialogPlace(` — const, line 132
- `const holder = useRef<Holder | null>(null)` — const, line 140
- `const frame = useRef(0)` — const, line 142
- `const changed = useRef(onChange)` — const, line 143
- `const windowsRef = useRef(windows)` — const, line 145
- `const hold = useRef<()` — const, line 148
- `const result = holder.current!.apply(root,` — const, line 151
- `const place = useRef<()` — const, line 159
- `const result = hold.current()` — const, line 161
- `const laidOut = root.ownerDocument.documentElement.getBoundingClientRect().width > 0` — const, line 163
- `const next = pillsOf(result, root, laidOut, desk.judging())` — const, line 164
- `const run = ()` — const, line 175
- `const schedule = ()` — const, line 181
- `const observer = new MutationObserver(()` — const, line 186
- `const pill = asking` — const, line 238

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `VeilLayer`; references `VeilLayer`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CheckVeilRefDto`
- [[Reference/Desktop/TypeScript/screens/desks/checks/controller|src/screens/desks/checks/controller.ts]] — import-or-re-export; imports `CheckDesk`
- [[Reference/Desktop/TypeScript/screens/desks/checks/hold|src/screens/desks/checks/hold.ts]] — import-or-re-export; imports `HeldRegion`, `HoldResult`, `HoldWindow`, `Holder`, `SAFE_ATTR`, `printOf`
- [[Reference/Desktop/TypeScript/screens/desks/checks/model|src/screens/desks/checks/model.ts]] — import-or-re-export; imports `VEIL_LABEL`, `costOf`, `refKey`, `veilSelector`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

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

1. Modify [apps/learnloop-tauri/src/screens/desks/checks/VeilLayer.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/VeilLayer.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
