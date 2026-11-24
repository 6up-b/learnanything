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
| Source lines | 729 |
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

- `export const COMPANION_MS =` — const, line 23
- `export interface CompanionContext` — interface, line 25
- `export interface CompanionChip` — interface, line 31
- `export interface CompanionHandle` — interface, line 35
- `export interface CompanionProps` — interface, line 42
- `export interface CompanionTutor` — interface, line 81
- `export const Companion = forwardRef<CompanionHandle, CompanionProps>(function Companion(props, ref)` — const, line 106
- `export function appendHistory(now: CompanionHistoryDto, page: CompanionHistoryDto): CompanionHistoryDto` — function, line 661

## Internal implementation anchors

- `function timeOf(ms: number): string` — function, line 91
- `function dayLabel(date: string): string` — function, line 95
- `const day = new Date(`$` — const, line 96
- `const today = new Date()` — const, line 97
- `function rectStyle(rect: Rect): CSSProperties` — function, line 102
- `const panelRef = useRef<HTMLDivElement | null>(null)` — const, line 113
- `const pillRef = useRef<HTMLButtonElement | null>(null)` — const, line 114
- `const tabRef = useRef<HTMLButtonElement | null>(null)` — const, line 115
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 116
- `const showing = state.mode !== "hidden"` — const, line 119
- `const restRect = state.mode === "anchored" && state.anchored ? state.anchored : dockRect(dock, stage)` — const, line 122
- `const lastShown = useRef<Rect | null>(null)` — const, line 124
- `const kind = state.last === "dissolve" ? "dissolve" : "hide"` — const, line 135
- `const handle = timers.set(()` — const, line 137
- `const panel = panelRef.current` — const, line 148
- `const previous = lastShown.current` — const, line 149
- `const dx = previous.x - shownRect.x` — const, line 154
- `const dy = previous.y - shownRect.y` — const, line 155
- `const sx = previous.w / Math.max(1, shownRect.w)` — const, line 156
- `const sy = previous.h / Math.max(1, shownRect.h)` — const, line 157
- `const panel = panelRef.current` — const, line 168
- `const pill = pillRef.current` — const, line 169
- `const tabEl = tabRef.current` — const, line 170
- `const target = pillRect(stage)` — const, line 191
- `const from = shownRect` — const, line 192
- `const k = q` — const, line 193
- `const tx = (target.x + target.w - (from.x + from.w)) * k` — const, line 196
- `const ty = (target.y + target.h - (from.y + from.h)) * k` — const, line 197
- `const s = 1 - (1 - target.w / Math.max(1, from.w)) * k` — const, line 198
- `const historyGeneration = useRef(0)` — const, line 214
- `const loadOlder = ()` — const, line 216
- `const cursor = history?.cursor` — const, line 217
- `const generation = historyGeneration.current` — const, line 219
- `let live = true` — let, line 236
- `const generation = ++historyGeneration.current` — const, line 237
- `const handle = timers.set(()` — const, line 239
- `const lastStatus = props.thread.length ? `$` — const, line 260
- `const body = bodyRef.current` — const, line 262
- `let live = true` — let, line 270
- `const drag = useRef<` — const, line 281
- `const onGrabDown = (event: React.PointerEvent<HTMLDivElement>)` — const, line 282
- `const onGrabMove = (event: React.PointerEvent<HTMLDivElement>)` — const, line 287
- `const d = drag.current` — const, line 288
- `const panel = panelRef.current` — const, line 289
- `const onGrabUp = (event: React.PointerEvent<HTMLDivElement>)` — const, line 294
- `const d = drag.current` — const, line 295
- `const panel = panelRef.current` — const, line 297
- `const dx = event.clientX - d.x` — const, line 299
- `const dy = event.clientY - d.y` — const, line 300
- `const dropped =` — const, line 301
- `const returnFocus = useRef<HTMLElement | null>(null)` — const, line 312
- `const panel = panelRef.current` — const, line 314
- `const active = document.activeElement` — const, line 326
- `const back = returnFocus.current` — const, line 333
- `const motionClass = reducedMotion ? " still" : ""` — const, line 339
- `const enter = state.last === "summon" ? " summon" : state.last === "show" ? " show" : ""` — const, line 340
- `const anchorOrigin = state.mode === "anchored" && state.anchored ? `$` — const, line 341
- `const tabRect = dockRect(dock, stage)` — const, line 343
- `const tabLabel = `◇ companion · $` — const, line 344
- `const question = draft.trim()` — const, line 455
- `function LookedUp(` — function, line 503
- `const view = exchange.answer?.tutor ?? null` — const, line 504
- `const excerpt = view.excerpt` — const, line 511
- `const send = ()` — const, line 512
- `function ExchangeView(` — function, line 564
- `let answer: ReactNode` — let, line 573
- `const days = now.days.map((day)` — const, line 662
- `const seen = new Set(days.flatMap((day)` — const, line 663
- `let into = days.find((each)` — let, line 665
- `let deskInto = into.desks.find((each)` — let, line 671
- `function HistoryView(` — function, line 686

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
- [[Reference/Desktop/TypeScript/screens/reader/TutorAnswer|src/screens/reader/TutorAnswer.tsx]] — import-or-re-export; imports `TUTOR_COPY`

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
