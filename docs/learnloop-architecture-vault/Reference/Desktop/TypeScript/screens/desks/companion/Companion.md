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
| Source lines | 523 |
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

- `export const COMPANION_MS =` — const, line 21
- `export interface CompanionContext` — interface, line 23
- `export interface CompanionChip` — interface, line 29
- `export interface CompanionHandle` — interface, line 33
- `export interface CompanionProps` — interface, line 40
- `export const Companion = forwardRef<CompanionHandle, CompanionProps>(function Companion(props, ref)` — const, line 88

## Internal implementation anchors

- `function timeOf(ms: number): string` — function, line 73
- `function dayLabel(date: string): string` — function, line 77
- `const day = new Date(`$` — const, line 78
- `const today = new Date()` — const, line 79
- `function rectStyle(rect: Rect): CSSProperties` — function, line 84
- `const panelRef = useRef<HTMLDivElement | null>(null)` — const, line 95
- `const pillRef = useRef<HTMLButtonElement | null>(null)` — const, line 96
- `const tabRef = useRef<HTMLButtonElement | null>(null)` — const, line 97
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 98
- `const showing = state.mode !== "hidden"` — const, line 101
- `const restRect = state.mode === "anchored" && state.anchored ? state.anchored : dockRect(dock, stage)` — const, line 104
- `const lastShown = useRef<Rect | null>(null)` — const, line 106
- `const kind = state.last === "dissolve" ? "dissolve" : "hide"` — const, line 117
- `const handle = timers.set(()` — const, line 119
- `const panel = panelRef.current` — const, line 130
- `const previous = lastShown.current` — const, line 131
- `const dx = previous.x - shownRect.x` — const, line 136
- `const dy = previous.y - shownRect.y` — const, line 137
- `const sx = previous.w / Math.max(1, shownRect.w)` — const, line 138
- `const sy = previous.h / Math.max(1, shownRect.h)` — const, line 139
- `const panel = panelRef.current` — const, line 150
- `const pill = pillRef.current` — const, line 151
- `const tabEl = tabRef.current` — const, line 152
- `const target = pillRect(stage)` — const, line 173
- `const from = shownRect` — const, line 174
- `const k = q` — const, line 175
- `const tx = (target.x + target.w - (from.x + from.w)) * k` — const, line 178
- `const ty = (target.y + target.h - (from.y + from.h)) * k` — const, line 179
- `const s = 1 - (1 - target.w / Math.max(1, from.w)) * k` — const, line 180
- `let live = true` — let, line 197
- `const handle = timers.set(()` — const, line 198
- `const lastStatus = props.thread.length ? `$` — const, line 219
- `const body = bodyRef.current` — const, line 221
- `let live = true` — let, line 229
- `const drag = useRef<` — const, line 240
- `const onGrabDown = (event: React.PointerEvent<HTMLDivElement>)` — const, line 241
- `const onGrabMove = (event: React.PointerEvent<HTMLDivElement>)` — const, line 246
- `const d = drag.current` — const, line 247
- `const panel = panelRef.current` — const, line 248
- `const onGrabUp = (event: React.PointerEvent<HTMLDivElement>)` — const, line 253
- `const d = drag.current` — const, line 254
- `const panel = panelRef.current` — const, line 256
- `const dx = event.clientX - d.x` — const, line 258
- `const dy = event.clientY - d.y` — const, line 259
- `const dropped =` — const, line 260
- `const motionClass = reducedMotion ? " still" : ""` — const, line 269
- `const enter = state.last === "summon" ? " summon" : state.last === "show" ? " show" : ""` — const, line 270
- `const anchorOrigin = state.mode === "anchored" && state.anchored ? `$` — const, line 271
- `const tabRect = dockRect(dock, stage)` — const, line 273
- `const tabLabel = `◇ tutor · $` — const, line 274
- `const question = draft.trim()` — const, line 363
- `function ExchangeView(` — function, line 409
- `let answer: ReactNode` — let, line 417
- `function HistoryView(` — function, line 485

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
