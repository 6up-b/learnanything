---
title: "Desktop module · src/screens/startBackdrops/ThreeBodyBackdrop.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.startBackdrops.ThreeBodyBackdrop"
language: "TypeScript"
area: "TypeScript/screens/startBackdrops"
source_path: "apps/learnloop-tauri/src/screens/startBackdrops/ThreeBodyBackdrop.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/startBackdrops/ThreeBodyBackdrop.tsx"
source_commit: "e3c6871bd2ed939ab9dcdf98d0ae9bdb19ded1ec"
source_commit_timestamp: "2026-07-23T15:53:16-05:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "Imported through StartScreen's supported optional backdrop paths reachable from src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/screens/startBackdrops/ThreeBodyBackdrop.tsx`

Area: [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ThreeBodyBackdrop` start-screen visualization or its rendering support.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/startBackdrops/ThreeBodyBackdrop.tsx](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/ThreeBodyBackdrop.tsx) |
| Source lines | 203 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `e3c6871bd2ed939ab9dcdf98d0ae9bdb19ded1ec` |
| Commit timestamp | `2026-07-23T15:53:16-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> Imported through StartScreen's supported optional backdrop paths reachable from src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/startBackdrops/ThreeBodyBackdrop|src/screens/startBackdrops/ThreeBodyBackdrop.tsx]]

## Public API

- `export function ThreeBodyBackdrop()` — function, line 61

## Internal implementation anchors

- `const DT = 0.008` — const, line 9
- `const SUBSTEPS = 6` — const, line 10
- `const SOFTENING2 = 1e-6` — const, line 11
- `const PERIOD = 6.3259` — const, line 12
- `type Body =` — type, line 14
- `function figure8(): Body[]` — function, line 16
- `const r1x = 0.97000436` — const, line 17
- `const r1y = -0.24308753` — const, line 18
- `const v3x = -0.93240737` — const, line 19
- `const v3y = -0.86473146` — const, line 20
- `function computeAccels(bodies: Body[])` — function, line 28
- `const dx = bodies[j].x - bodies[i].x` — const, line 35
- `const dy = bodies[j].y - bodies[i].y` — const, line 36
- `const r2 = dx * dx + dy * dy + SOFTENING2` — const, line 37
- `const inv = 1 / (Math.sqrt(r2) * r2)` — const, line 38
- `function verletStep(bodies: Body[], dt: number)` — function, line 47
- `const ref = useRef<HTMLCanvasElement>(null)` — const, line 62
- `const canvas = ref.current` — const, line 65
- `const ctx = canvas.getContext("2d")` — const, line 67
- `const P = readPaletteColors()` — const, line 70
- `const bgDeep = mixRgb(P.bg, BLACK, 0.55)` — const, line 71
- `const accents: Rgb[] = [P.amber, P.cyan, P.pink]` — const, line 72
- `const reduce = prefersReducedMotion()` — const, line 73
- `let raf = 0` — let, line 75
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 76
- `let bodies = figure8()` — let, line 77
- `let steps = 0` — let, line 79
- `let viewAngle = 0` — let, line 80
- `function prime()` — function, line 82
- `const w = canvas!.width / dpr` — const, line 83
- `const h = canvas!.height / dpr` — const, line 84
- `function reset()` — function, line 90
- `function project(b: Body)` — function, line 97
- `const w = canvas!.width / dpr` — const, line 98
- `const h = canvas!.height / dpr` — const, line 99
- `const cosA = Math.cos(viewAngle)` — const, line 101
- `const sinA = Math.sin(viewAngle)` — const, line 102
- `const rx = b.x * cosA - b.y * sinA` — const, line 103
- `const ry = b.x * sinA + b.y * cosA` — const, line 104
- `const scale = Math.min(w / 3.4, h / 2.0)` — const, line 105
- `function drawBodies(trailOnly: boolean)` — function, line 109
- `const c = accents[i]` — const, line 112
- `function safetyCheck()` — function, line 132
- `function resize()` — function, line 143
- `const rect = canvas!.getBoundingClientRect()` — const, line 144
- `function staticFrame()` — function, line 152
- `const n = Math.ceil(PERIOD / DT)` — const, line 156
- `const ro = new ResizeObserver(()` — const, line 167
- `function frame()` — function, line 176
- `const w = canvas!.width / dpr` — const, line 177
- `const h = canvas!.height / dpr` — const, line 178

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `ThreeBodyBackdrop`; references `ThreeBodyBackdrop`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/startBackdrops/shared|src/screens/startBackdrops/shared.ts]] — import-or-re-export; imports `BLACK`, `Rgb`, `mixRgb`, `prefersReducedMotion`, `readPaletteColors`, `rgba`

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

1. Modify [apps/learnloop-tauri/src/screens/startBackdrops/ThreeBodyBackdrop.tsx](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/ThreeBodyBackdrop.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
