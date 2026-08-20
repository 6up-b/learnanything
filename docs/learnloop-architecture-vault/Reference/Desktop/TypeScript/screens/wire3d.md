---
title: "Desktop module · src/screens/wire3d.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.wire3d"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/wire3d.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/wire3d.ts"
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

# `src/screens/wire3d.ts`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `Cam`, `Viewport`, `Projected`, `project` and related exports within the desktop's TypeScript/screens ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/wire3d.ts](../../../../../../apps/learnloop-tauri/src/screens/wire3d.ts) |
| Source lines | 182 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/wire3d|src/screens/wire3d.ts]]

## Public API

- `export interface Cam` — interface, line 13
- `export interface Viewport` — interface, line 18
- `export interface Projected` — interface, line 26
- `export function project(x: number, y: number, z: number, cam: Cam, view: Viewport): Projected` — function, line 35
- `export function depthFade(depth: number, lo = 0.5, hi = 1): number` — function, line 50
- `export function useOrbitCamera(initial: Cam =` — function, line 61
- `export function useElementSize<T extends Element>():` — function, line 153
- `export function polyPath(points: Projected[], close = false): string` — function, line 178

## Internal implementation anchors

- `const cyaw = Math.cos(cam.yaw)` — const, line 36
- `const syaw = Math.sin(cam.yaw)` — const, line 37
- `const x1 = x * cyaw - y * syaw` — const, line 38
- `const y1 = x * syaw + y * cyaw` — const, line 39
- `const cp = Math.cos(cam.pitch)` — const, line 40
- `const sp = Math.sin(cam.pitch)` — const, line 41
- `const sy = y1 * cp - z * sp` — const, line 42
- `const depth = z * cp - y1 * sp` — const, line 43
- `const persp = view.persp ?? 5` — const, line 44
- `const k = persp / Math.max(0.5, persp - depth)` — const, line 45
- `const t = Math.max(0, Math.min(1, (depth + 1.4) / 2.8))` — const, line 51
- `const clampPitch = (value: number)` — const, line 55
- `const drag = useRef<` — const, line 63
- `const dragRaf = useRef(0)` — const, line 64
- `const pendingDrag = useRef<` — const, line 65
- `const quietUntil = useRef(0)` — const, line 66
- `let raf = 0` — let, line 70
- `let prev = performance.now()` — let, line 71
- `const tick = (now: number)` — const, line 72
- `const dt = Math.min(64, now - prev)` — const, line 73
- `const pauseDrift = (ms = 2600)` — const, line 89
- `const onMouseDown = (event: ReactMouseEvent)` — const, line 93
- `const applyDrag = (point:` — const, line 103
- `const d = drag.current` — const, line 104
- `const flushDrag = ()` — const, line 112
- `const point = pendingDrag.current` — const, line 114
- `const move = (e: MouseEvent)` — const, line 119
- `const up = ()` — const, line 127
- `const point = pendingDrag.current` — const, line 130
- `const ref = useCallback((el: T | null)` — const, line 156
- `const measure = ()` — const, line 160
- `const rect = node.getBoundingClientRect()` — const, line 161
- `const observer = new ResizeObserver(measure)` — const, line 169
- `const body = points.map((p, i)` — const, line 180

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `useElementSize`; references `useElementSize`
- [[Reference/Desktop/TypeScript/screens/KnowledgeTerrainView|src/screens/KnowledgeTerrainView.tsx]] — import-or-re-export: `depthFade`, `project`, `useOrbitCamera`; references `depthFade`, `project`, `useOrbitCamera`
- [[Reference/Desktop/TypeScript/screens/KnowledgeWellView|src/screens/KnowledgeWellView.tsx]] — import-or-re-export: `Projected`, `depthFade`, `polyPath`, `project`, `useOrbitCamera`; references `Projected`, `depthFade`, `polyPath`, `project`, `useOrbitCamera`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_exam_calibration.py](../../../../../../tests/test_exam_calibration.py) — cross-boundary name contract: references uniquely owned exported name `Projected`; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/wire3d.ts](../../../../../../apps/learnloop-tauri/src/screens/wire3d.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
