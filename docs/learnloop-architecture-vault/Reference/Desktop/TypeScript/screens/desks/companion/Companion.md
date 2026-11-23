---
title: "Desktop module · src/screens/desks/companion/Companion.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.companion.Companion"
language: "TypeScript"
area: "TypeScript/screens/desks/companion"
source_path: "apps/learnloop-tauri/src/screens/desks/companion/Companion.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/companion/Companion.tsx"
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

# `src/screens/desks/companion/Companion.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/companion/_area|TypeScript/screens/desks/companion]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `Companion` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/companion/Companion.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/Companion.tsx) |
| Source lines | 524 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/companion/_area|TypeScript/screens/desks/companion]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/companion/Companion|src/screens/desks/companion/Companion.tsx]]

## Public API

- `export const COMPANION_MS =` — const, line 22
- `export interface CompanionContext` — interface, line 24
- `export interface CompanionChip` — interface, line 30
- `export interface CompanionHandle` — interface, line 34
- `export interface CompanionProps` — interface, line 41
- `export const Companion = forwardRef<CompanionHandle, CompanionProps>(function Companion(props, ref)` — const, line 89

## Internal implementation anchors

- `function timeOf(ms: number): string` — function, line 74
- `function dayLabel(date: string): string` — function, line 78
- `const day = new Date(`$` — const, line 79
- `const today = new Date()` — const, line 80
- `function rectStyle(rect: Rect): CSSProperties` — function, line 85
- `const panelRef = useRef<HTMLDivElement | null>(null)` — const, line 96
- `const pillRef = useRef<HTMLButtonElement | null>(null)` — const, line 97
- `const tabRef = useRef<HTMLButtonElement | null>(null)` — const, line 98
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 99
- `const showing = state.mode !== "hidden"` — const, line 102
- `const restRect = state.mode === "anchored" && state.anchored ? state.anchored : dockRect(dock, stage)` — const, line 105
- `const lastShown = useRef<Rect | null>(null)` — const, line 107
- `const kind = state.last === "dissolve" ? "dissolve" : "hide"` — const, line 118
- `const handle = timers.set(()` — const, line 120
- `const panel = panelRef.current` — const, line 131
- `const previous = lastShown.current` — const, line 132
- `const dx = previous.x - shownRect.x` — const, line 137
- `const dy = previous.y - shownRect.y` — const, line 138
- `const sx = previous.w / Math.max(1, shownRect.w)` — const, line 139
- `const sy = previous.h / Math.max(1, shownRect.h)` — const, line 140
- `const panel = panelRef.current` — const, line 151
- `const pill = pillRef.current` — const, line 152
- `const tabEl = tabRef.current` — const, line 153
- `const target = pillRect(stage)` — const, line 174
- `const from = shownRect` — const, line 175
- `const k = q` — const, line 176
- `const tx = (target.x + target.w - (from.x + from.w)) * k` — const, line 179
- `const ty = (target.y + target.h - (from.y + from.h)) * k` — const, line 180
- `const s = 1 - (1 - target.w / Math.max(1, from.w)) * k` — const, line 181
- `let live = true` — let, line 198
- `const handle = timers.set(()` — const, line 199
- `const lastStatus = props.thread.length ? `$` — const, line 220
- `const body = bodyRef.current` — const, line 222
- `let live = true` — let, line 230
- `const drag = useRef<` — const, line 241
- `const onGrabDown = (event: React.PointerEvent<HTMLDivElement>)` — const, line 242
- `const onGrabMove = (event: React.PointerEvent<HTMLDivElement>)` — const, line 247
- `const d = drag.current` — const, line 248
- `const panel = panelRef.current` — const, line 249
- `const onGrabUp = (event: React.PointerEvent<HTMLDivElement>)` — const, line 254
- `const d = drag.current` — const, line 255
- `const panel = panelRef.current` — const, line 257
- `const dx = event.clientX - d.x` — const, line 259
- `const dy = event.clientY - d.y` — const, line 260
- `const dropped =` — const, line 261
- `const motionClass = reducedMotion ? " still" : ""` — const, line 270
- `const enter = state.last === "summon" ? " summon" : state.last === "show" ? " show" : ""` — const, line 271
- `const anchorOrigin = state.mode === "anchored" && state.anchored ? `$` — const, line 272
- `const tabRect = dockRect(dock, stage)` — const, line 274
- `const tabLabel = `◇ tutor · $` — const, line 275
- `const question = draft.trim()` — const, line 364
- `function ExchangeView(` — function, line 410
- `let answer: ReactNode` — let, line 418
- `function HistoryView(` — function, line 486

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `Companion`, `CompanionHandle`; references `Companion`, `CompanionHandle`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CompanionDock`, `CompanionExchangeDto`, `CompanionHistoryDto`, `TutorCitationDto`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/desks/companion/DiffProposal|src/screens/desks/companion/DiffProposal.tsx]] — import-or-re-export; imports `DiffProposal`, `ProposedDiff`
- [[Reference/Desktop/TypeScript/screens/desks/companion/asks|src/screens/desks/companion/asks.ts]] — import-or-re-export; imports `CompanionExchange`
- [[Reference/Desktop/TypeScript/screens/desks/companion/model|src/screens/desks/companion/model.ts]] — import-or-re-export; imports `CompanionState`, `dockRect`, `nearestDock`, `pillRect`
- [[Reference/Desktop/TypeScript/screens/desks/fitMath|src/screens/desks/fitMath.tsx]] — import-or-re-export; imports `FitMath`
- [[Reference/Desktop/TypeScript/screens/desks/geometry|src/screens/desks/geometry.ts]] — import-or-re-export; imports `Rect`, `Stage`
- [[Reference/Desktop/TypeScript/screens/desks/keys/router|src/screens/desks/keys/router.ts]] — import-or-re-export; imports `Timers`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/companion/Companion.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/Companion.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/companion/Companion.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/Companion.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
