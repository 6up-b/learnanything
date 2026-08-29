---
title: "Desktop module · src/screens/startBackdrops/PendulumBackdrop.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.startBackdrops.PendulumBackdrop"
language: "TypeScript"
area: "TypeScript/screens/startBackdrops"
source_path: "apps/learnloop-tauri/src/screens/startBackdrops/PendulumBackdrop.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/startBackdrops/PendulumBackdrop.tsx"
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

# `src/screens/startBackdrops/PendulumBackdrop.tsx`

Area: [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `PendulumBackdrop` start-screen visualization or its rendering support.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/startBackdrops/PendulumBackdrop.tsx](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/PendulumBackdrop.tsx) |
| Source lines | 225 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/startBackdrops/PendulumBackdrop|src/screens/startBackdrops/PendulumBackdrop.tsx]]

## Public API

- `export function PendulumBackdrop()` — function, line 60

## Internal implementation anchors

- `const N_PENDULUMS = 5` — const, line 10
- `const G = 9.81` — const, line 11
- `const DT = 1 / 240` — const, line 12
- `const SUBSTEPS = 4` — const, line 13
- `const RESEED_MS = 180_000` — const, line 14
- `type State =` — type, line 16
- `function accel(s: State): [number, number]` — function, line 25
- `const d = th1 - th2` — const, line 27
- `const cd = Math.cos(d)` — const, line 28
- `const sd = Math.sin(d)` — const, line 29
- `const den = 3 - Math.cos(2 * d)` — const, line 30
- `const a1 = (-3 * G * Math.sin(th1) - G * Math.sin(th1 - 2 * th2) - 2 * sd * (w2 * w2 + w1 * w1 * cd)) / den` — const, line 31
- `const a2 = (2 * sd * (2 * w1 * w1 + 2 * G * Math.cos(th1) + w2 * w2 * cd)) / den` — const, line 32
- `function deriv(s: State): State` — function, line 36
- `function rk4(s: State, dt: number): State` — function, line 41
- `const add = (a: State, b: State, k: number): State` — const, line 42
- `const k1 = deriv(s)` — const, line 48
- `const k2 = deriv(add(s, k1, dt / 2))` — const, line 49
- `const k3 = deriv(add(s, k2, dt / 2))` — const, line 50
- `const k4 = deriv(add(s, k3, dt))` — const, line 51
- `const trailRef = useRef<HTMLCanvasElement>(null)` — const, line 61
- `const armRef = useRef<HTMLCanvasElement>(null)` — const, line 62
- `const trailCanvas = trailRef.current` — const, line 65
- `const armCanvas = armRef.current` — const, line 66
- `const trailCtx = trailCanvas.getContext("2d")` — const, line 68
- `const armCtx = armCanvas.getContext("2d")` — const, line 69
- `const P = readPaletteColors()` — const, line 72
- `const bgDeep = mixRgb(P.bg, BLACK, 0.55)` — const, line 73
- `const accents: Rgb[] = [P.amber, P.green, P.cyan, P.pink, P.red]` — const, line 74
- `const reduce = prefersReducedMotion()` — const, line 75
- `let raf = 0` — let, line 77
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 78
- `let pendulums: State[] = []` — let, line 79
- `let seededAt = 0` — let, line 80
- `function seed()` — function, line 82
- `const th1 = (0.6 + Math.random() * 0.3) * Math.PI` — const, line 83
- `function primeTrail()` — function, line 94
- `const w = trailCanvas!.width / dpr` — const, line 95
- `const h = trailCanvas!.height / dpr` — const, line 96
- `function geometry()` — function, line 102
- `const w = armCanvas!.width / dpr` — const, line 103
- `const h = armCanvas!.height / dpr` — const, line 104
- `function tipOf(s: State, g: ReturnType<typeof geometry>)` — function, line 108
- `const x1 = g.ax + g.arm * Math.sin(s.th1)` — const, line 109
- `const y1 = g.ay + g.arm * Math.cos(s.th1)` — const, line 110
- `const x2 = x1 + g.arm * Math.sin(s.th2)` — const, line 111
- `const y2 = y1 + g.arm * Math.cos(s.th2)` — const, line 112
- `function stepAll(substeps: number)` — function, line 116
- `let s = pendulums[i]` — let, line 118
- `const blown = pendulums.some((s)` — const, line 123
- `function drawTrails()` — function, line 127
- `const g = geometry()` — const, line 128
- `function drawArms()` — function, line 139
- `const g = geometry()` — const, line 140
- `const c = accents[i % accents.length]` — const, line 144
- `function staticFrame()` — function, line 163
- `const g = geometry()` — const, line 165
- `function resize()` — function, line 177
- `const rect = armCanvas!.getBoundingClientRect()` — const, line 178
- `const ro = new ResizeObserver(()` — const, line 192
- `function frame()` — function, line 201
- `const style =` — const, line 218

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `PendulumBackdrop`; references `PendulumBackdrop`

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

1. Modify [apps/learnloop-tauri/src/screens/startBackdrops/PendulumBackdrop.tsx](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/PendulumBackdrop.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
