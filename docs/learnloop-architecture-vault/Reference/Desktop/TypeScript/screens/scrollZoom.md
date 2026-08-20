---
title: "Desktop module · src/screens/scrollZoom.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.scrollZoom"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/scrollZoom.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/scrollZoom.ts"
source_commit: "971d7c274e09873d726d43578cd080e4d8865571"
source_commit_timestamp: "2026-07-27T06:01:19-04:00"
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

# `src/screens/scrollZoom.ts`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SCROLL_ZOOM`, `ScrollZoomOptions`, `ScrollZoom`, `useScrollZoom` within the desktop's TypeScript/screens ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/scrollZoom.ts](../../../../../../apps/learnloop-tauri/src/screens/scrollZoom.ts) |
| Source lines | 242 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `971d7c274e09873d726d43578cd080e4d8865571` |
| Commit timestamp | `2026-07-27T06:01:19-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeWellView|src/screens/KnowledgeWellView.tsx]] → [[Reference/Desktop/TypeScript/screens/scrollZoom|src/screens/scrollZoom.ts]]

## Public API

- `export const SCROLL_ZOOM =` — const, line 21
- `export interface ScrollZoomOptions` — interface, line 47
- `export interface ScrollZoom` — interface, line 61
- `export function useScrollZoom(options: ScrollZoomOptions): ScrollZoom` — function, line 90

## Internal implementation anchors

- `interface Frame` — interface, line 81
- `const REST: Frame =` — const, line 87
- `const clamp = (value: number, lo: number, hi: number)` — const, line 88
- `const enabled = options.enabled ?? SCROLL_ZOOM.enabled` — const, line 91
- `const opts = useRef(options)` — const, line 92
- `const live = useRef<Frame>(REST)` — const, line 97
- `const target = useRef<Frame>(REST)` — const, line 98
- `const touchedAt = useRef(-Infinity)` — const, line 99
- `const raf = useRef(0)` — const, line 100
- `const element = useRef<SVGSVGElement | null>(null)` — const, line 101
- `const fadeAt = (now: number)` — const, line 103
- `const age = now - touchedAt.current` — const, line 104
- `const fade = age <= SCROLL_ZOOM.holdMs ? 1 : 1 - (age - SCROLL_ZOOM.holdMs) / SCROLL_ZOOM.fadeMs` — const, line 105
- `const floor = target.current.k === 1 && live.current.k === 1 ? 0 : SCROLL_ZOOM.restOpacity` — const, line 106
- `const pump = useCallback(()` — const, line 112
- `let prev = performance.now()` — let, line 114
- `const tick = (now: number)` — const, line 115
- `const dt = Math.min(64, now - prev)` — const, line 116
- `const from = live.current` — const, line 118
- `const to = target.current` — const, line 119
- `const t = SCROLL_ZOOM.animated ? 1 - Math.pow(1 - SCROLL_ZOOM.lerp, dt / 16.667) : 1` — const, line 120
- `let next: Frame =` — let, line 121
- `const settled = Math.abs(next.k - to.k) <= SCROLL_ZOOM.settleEps * to.k && Math.abs(next.panX - to.panX) <= 0.2 && Math.abs(next.panY - to.panY) <= 0.2` — const, line 126
- `const fade = fadeAt(now)` — const, line 132
- `const readoutFloor = to.k === 1 && next.k === 1 ? 0 : SCROLL_ZOOM.restOpacity` — const, line 133
- `const readoutSettled = Math.abs(fade - readoutFloor) <= 0.001` — const, line 134
- `const aim = useCallback( (next: Frame)` — const, line 145
- `const reset = useCallback(()` — const, line 154
- `const zoomBy = useCallback( (factor: number, ax?: number, ay?: number)` — const, line 161
- `const cfg = opts.current` — const, line 163
- `const previous = target.current` — const, line 164
- `const k = clamp(previous.k * factor, SCROLL_ZOOM.min, SCROLL_ZOOM.max)` — const, line 165
- `const f = k / previous.k` — const, line 166
- `const anchorX = ax ?? cfg.centerX` — const, line 167
- `const anchorY = ay ?? cfg.centerY` — const, line 168
- `const leash = Math.max(0, k - 1) * cfg.contentRadius * SCROLL_ZOOM.panLeash` — const, line 169
- `const onWheel = useRef((event: WheelEvent)` — const, line 184
- `const el = element.current` — const, line 185
- `const rect = el.getBoundingClientRect()` — const, line 188
- `const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? rect.height : 1` — const, line 190
- `const factor = Math.exp(-event.deltaY * unit * SCROLL_ZOOM.wheelGain)` — const, line 191
- `const toViewBox = opts.current.viewWidth / rect.width` — const, line 196
- `const ref = useCallback((el: SVGSVGElement | null)` — const, line 206
- `const listener = (event: WheelEvent)` — const, line 213
- `const noop = useCallback(()` — const, line 225

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/KnowledgeWellView|src/screens/KnowledgeWellView.tsx]] — import-or-re-export: `useScrollZoom`; references `useScrollZoom`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/scrollZoom.ts](../../../../../../apps/learnloop-tauri/src/screens/scrollZoom.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
